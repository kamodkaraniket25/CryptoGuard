"""Live OSV.dev queries. https://api.osv.dev/v1/query"""

from urllib.parse import quote

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import NO_MATCH_MESSAGE
from app.services.cache import get_cached, store_cache
from app.services.http_client import http_client
from app.utils.timeutil import isoformat_utc, utcnow


def canonical_finding_id(advisory_id: str, aliases: list[str]) -> str:
    for alias in aliases:
        if isinstance(alias, str) and alias.startswith("CVE-"):
            return alias
    if advisory_id.startswith("CVE-"):
        return advisory_id
    return advisory_id


def _reported_severity(vuln: dict) -> tuple[list[dict], str | None]:
    """Copy severity fields OSV actually returned. Do not score a vector locally."""
    reported: list[dict] = []
    raw = vuln.get("severity")
    if isinstance(raw, list):
        for entry in raw[:6]:
            if not isinstance(entry, dict):
                continue
            score = entry.get("score")
            if not isinstance(score, str) or not score.strip():
                continue
            kind = entry.get("type")
            reported.append(
                {
                    "type": str(kind)[:40] if isinstance(kind, str) and kind.strip() else None,
                    "score": score.strip()[:240],
                }
            )
    label = None
    database = vuln.get("database_specific")
    if isinstance(database, dict):
        value = database.get("severity")
        if isinstance(value, str) and value.strip():
            label = value.strip()[:40]
    return reported, label


def parse_vulnerability(vuln: dict) -> dict:
    references = vuln.get("references") if isinstance(vuln.get("references"), list) else []
    reference_url = None
    for item in references:
        if isinstance(item, dict) and isinstance(item.get("url"), str):
            reference_url = item["url"][:500]
            break
    affected = []
    for entry in (vuln.get("affected") or [])[:8]:
        if not isinstance(entry, dict):
            continue
        package = entry.get("package") if isinstance(entry.get("package"), dict) else {}
        versions = entry.get("versions") if isinstance(entry.get("versions"), list) else []
        ranges = []
        for item in (entry.get("ranges") or [])[:4]:
            if not isinstance(item, dict):
                continue
            events = []
            for event in (item.get("events") or [])[:8]:
                if isinstance(event, dict):
                    events.append({key: value for key, value in event.items() if key in {"introduced", "fixed", "last_affected", "limit"}})
            ranges.append({"type": item.get("type"), "events": events})
        affected.append(
            {
                "package": package.get("name"),
                "ecosystem": package.get("ecosystem"),
                "versions": [str(item) for item in versions[:15]],
                "version_count": len(versions),
                "ranges": ranges,
            }
        )
    advisory_id = str(vuln.get("id") or "")
    aliases = [str(item) for item in vuln.get("aliases") or [] if isinstance(item, str)]
    summary = vuln.get("summary") if isinstance(vuln.get("summary"), str) else ""
    if not summary and isinstance(vuln.get("details"), str):
        summary = vuln["details"][:400]
    severity, severity_label = _reported_severity(vuln)
    return {
        "id": advisory_id,
        "summary": summary[:500],
        "modified": vuln.get("modified"),
        "published": vuln.get("published"),
        "aliases": aliases[:20],
        "reference_url": reference_url,
        "osv_url": f"https://osv.dev/vulnerability/{quote(advisory_id)}" if advisory_id else None,
        "affected": affected,
        "severity": severity,
        "severity_label": severity_label,
        "canonical_id": canonical_finding_id(advisory_id, aliases),
        "source": "osv",
    }


async def query_osv_package(name: str, ecosystem: str, version: str) -> dict:
    settings = get_settings()
    base_payload = {"package": {"name": name, "ecosystem": ecosystem}, "version": version}
    advisories: list[dict] = []
    truncated = False
    token = None
    pages = 0
    try:
        async with http_client(settings.osv_timeout_seconds) as client:
            while pages < settings.osv_max_pages:
                pages += 1
                payload = dict(base_payload)
                if token:
                    payload["page_token"] = token
                response = await client.post(settings.osv_query_url, json=payload)
                if response.status_code != 200:
                    return _error(
                        f"OSV returned HTTP {response.status_code}.",
                        "http_error",
                    )
                try:
                    body = response.json()
                except ValueError:
                    return _error("OSV returned a response that was not JSON.", "invalid_response")
                if not isinstance(body, dict):
                    return _error("OSV returned an unexpected JSON value.", "invalid_response")
                for vuln in body.get("vulns") or []:
                    if isinstance(vuln, dict):
                        advisories.append(parse_vulnerability(vuln))
                token = body.get("next_page_token")
                if not token:
                    break
            else:
                if token:
                    truncated = True
    except httpx.TimeoutException:
        return _error("The OSV request timed out.", "timeout")
    except httpx.HTTPError:
        return _error("The OSV request failed before a response was received.", "network")
    return {
        "query_status": "ok",
        "advisories": advisories,
        "truncated": truncated,
        "message": None if advisories else NO_MATCH_MESSAGE,
        "error_category": None,
    }


def _error(message: str, category: str) -> dict:
    return {
        "query_status": "error",
        "advisories": [],
        "truncated": False,
        "message": message + " This does not mean the package has no vulnerabilities.",
        "error_category": category,
    }


async def lookup_package(
    db: Session,
    *,
    name: str,
    ecosystem: str,
    version: str,
    refresh: bool = False,
    memo: dict | None = None,
) -> dict:
    key = (ecosystem, name, version)
    if memo is not None and key in memo and not refresh:
        return memo[key]
    cached = None if refresh else get_cached(db, "osv", name, ecosystem, version)
    if cached is not None:
        payload = cached["payload"]
        result = {
            "query_status": "ok",
            "cached": True,
            "retrieved_at": isoformat_utc(cached["retrieved_at"]),
            "advisories": payload.get("advisories") or [],
            "truncated": bool(payload.get("truncated")),
            "message": payload.get("message"),
            "error_category": None,
            "source": "osv",
        }
    else:
        live = await query_osv_package(name, ecosystem, version)
        retrieved = isoformat_utc(utcnow())
        if live["query_status"] == "ok":
            store_cache(
                db,
                source="osv",
                package_name=name,
                ecosystem=ecosystem,
                version=version,
                payload={
                    "advisories": live["advisories"],
                    "truncated": live["truncated"],
                    "message": live["message"],
                },
            )
        result = {
            **live,
            "cached": False,
            "retrieved_at": retrieved if live["query_status"] == "ok" else None,
            "source": "osv",
        }
    if memo is not None:
        memo[key] = result
    return result
