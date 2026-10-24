"""Optional NVD CVE API 2.0 lookups. OSV does not depend on this service."""

import asyncio
import re
import time

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.cache import get_cached, store_cache
from app.services.http_client import http_client
from app.utils.timeutil import isoformat_utc, utcnow

CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$")
_last_request = 0.0
_lock = asyncio.Lock()


def validate_cve_id(value: str) -> str:
    candidate = value.strip().upper()
    if not CVE_RE.fullmatch(candidate):
        raise ValueError("Enter a CVE identifier such as CVE-2021-44228.")
    return candidate


async def _pace() -> None:
    global _last_request
    interval = get_settings().nvd_min_interval_seconds
    async with _lock:
        elapsed = time.monotonic() - _last_request
        if elapsed < interval:
            await asyncio.sleep(interval - elapsed)
        _last_request = time.monotonic()


def reset_pacing() -> None:
    global _last_request
    _last_request = 0.0


def parse_cve_record(body: dict) -> dict | None:
    vulnerabilities = body.get("vulnerabilities") if isinstance(body, dict) else None
    if not isinstance(vulnerabilities, list) or not vulnerabilities:
        return None
    wrapper = vulnerabilities[0] if isinstance(vulnerabilities[0], dict) else {}
    cve = wrapper.get("cve") if isinstance(wrapper.get("cve"), dict) else {}
    descriptions = cve.get("descriptions") if isinstance(cve.get("descriptions"), list) else []
    summary = None
    for item in descriptions:
        if isinstance(item, dict) and item.get("lang") == "en" and isinstance(item.get("value"), str):
            summary = item["value"][:500]
            break
    references = cve.get("references") if isinstance(cve.get("references"), list) else []
    reference_url = None
    for item in references:
        if isinstance(item, dict) and isinstance(item.get("url"), str):
            reference_url = item["url"][:500]
            break
    severity = None
    score = None
    metrics = cve.get("metrics") if isinstance(cve.get("metrics"), dict) else {}
    for key in ("cvssMetricV31", "cvssMetricV30"):
        entries = metrics.get(key)
        if isinstance(entries, list) and entries and isinstance(entries[0], dict):
            data = entries[0].get("cvssData") if isinstance(entries[0].get("cvssData"), dict) else {}
            severity = data.get("baseSeverity")
            score = data.get("baseScore")
            break
    cve_id = cve.get("id")
    if not isinstance(cve_id, str):
        return None
    return {
        "id": cve_id,
        "summary": summary,
        "published": cve.get("published"),
        "modified": cve.get("lastModified"),
        "reference_url": reference_url,
        "nvd_url": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
        "cvss_score": score,
        "cvss_severity": severity,
        "source": "nvd",
        "canonical_id": cve_id,
    }


async def query_nvd_cve(cve_id: str) -> dict:
    settings = get_settings()
    await _pace()
    headers = {}
    if settings.nvd_key_configured:
        headers["apiKey"] = settings.nvd_api_key.strip()
    try:
        async with http_client(settings.nvd_timeout_seconds) as client:
            response = await client.get(
                settings.nvd_api_url,
                params={"cveId": cve_id},
                headers=headers,
            )
    except httpx.TimeoutException:
        return {"query_status": "error", "message": "The NVD request timed out.", "error_category": "timeout", "record": None}
    except httpx.HTTPError:
        return {
            "query_status": "error",
            "message": "The NVD request failed before a response was received.",
            "error_category": "network",
            "record": None,
        }
    if response.status_code == 429:
        return {
            "query_status": "error",
            "message": "NVD rate limited this request. Try again later. This is not a statement about the CVE.",
            "error_category": "rate_limit",
            "record": None,
        }
    if response.status_code != 200:
        return {
            "query_status": "error",
            "message": f"NVD returned HTTP {response.status_code}.",
            "error_category": "http_error",
            "record": None,
        }
    try:
        body = response.json()
    except ValueError:
        return {"query_status": "error", "message": "NVD returned a response that was not JSON.", "error_category": "invalid_response", "record": None}
    record = parse_cve_record(body)
    if record is None:
        return {
            "query_status": "ok",
            "message": "No matching CVE record returned by NVD for this identifier.",
            "error_category": None,
            "record": None,
        }
    return {"query_status": "ok", "message": None, "error_category": None, "record": record}


async def lookup_cve(db: Session, cve_id: str, refresh: bool = False) -> dict:
    if not get_settings().nvd_enabled:
        return {
            "query_status": "disabled",
            "message": "NVD lookups are disabled. Set NVD_ENABLED=true on the backend. OSV queries do not need this setting.",
            "error_category": "disabled",
            "record": None,
            "cached": False,
            "retrieved_at": None,
            "source": "nvd",
        }
    cached = None if refresh else get_cached(db, "nvd", cve_id, "cve", "-")
    if cached is not None:
        payload = cached["payload"]
        return {
            "query_status": payload.get("query_status", "ok"),
            "message": payload.get("message"),
            "error_category": None,
            "record": payload.get("record"),
            "cached": True,
            "retrieved_at": isoformat_utc(cached["retrieved_at"]),
            "source": "nvd",
        }
    live = await query_nvd_cve(cve_id)
    retrieved = isoformat_utc(utcnow()) if live["query_status"] == "ok" else None
    if live["query_status"] == "ok":
        store_cache(
            db,
            source="nvd",
            package_name=cve_id,
            ecosystem="cve",
            version="-",
            payload={"query_status": "ok", "message": live["message"], "record": live["record"]},
        )
    return {**live, "cached": False, "retrieved_at": retrieved, "source": "nvd"}
