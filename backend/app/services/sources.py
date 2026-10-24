"""Data-source catalog and bounded live status checks."""

import time

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.tables import DataSourceCheck
from app.services.http_client import http_client
from app.utils.timeutil import isoformat_utc, utcnow

SOURCE_IDS = ("osv", "nvd", "cyclonedx")

CATALOG = [
    {
        "id": "osv",
        "name": "OSV Vulnerability Database",
        "website": "https://osv.dev/",
        "documentation_url": "https://google.github.io/osv.dev/api/",
        "endpoint": "https://api.osv.dev/v1/query",
        "category": "Vulnerability database",
        "purpose": "Query known vulnerabilities by package name, ecosystem, and version, and read advisory identifiers, summaries, affected-package information, and references when OSV provides them.",
        "access_method": "Live HTTP API integration",
        "fields_used": ["id", "summary", "details", "modified", "published", "aliases", "references", "affected", "next_page_token"],
        "limitations": [
            "CryptoGuard calls POST /v1/query because that response can include summaries, references, and affected packages. The batch endpoint returns only identifiers and modified times.",
            "No matching advisory is not proof that a package has no vulnerabilities.",
            "Results are case-sensitive. npm packages keep their declared names. PyPI names are normalized with PEP 503 rules before the query.",
        ],
        "attribution": "CryptoGuard does not bundle the OSV database. It queries the public API. Individual advisories come from upstream databases; see https://osv.dev/ for attribution of each record.",
        "license_note": "Consult https://osv.dev/ for the current terms that apply to the service and to individual advisory records. CryptoGuard does not redistribute a bulk copy.",
        "data_is_downloaded": False,
    },
    {
        "id": "nvd",
        "name": "National Vulnerability Database (NVD)",
        "website": "https://nvd.nist.gov/",
        "documentation_url": "https://nvd.nist.gov/developers/vulnerabilities",
        "endpoint": "https://services.nvd.nist.gov/rest/json/cves/2.0",
        "category": "Vulnerability database",
        "purpose": "Optional second source for a CVE record, including its English description, dates, references, and CVSS data when NVD includes them.",
        "access_method": "NVD CVE API 2.0, used only when NVD_ENABLED=true for lookups. Status checks can run while lookups are disabled.",
        "fields_used": ["vulnerabilities[].cve.id", "descriptions", "published", "lastModified", "references", "metrics.cvssMetricV31", "metrics.cvssMetricV30"],
        "limitations": [
            "NVD is not required for the OSV workflow.",
            "CryptoGuard looks up CVE identifiers. It does not download the NVD data feeds at startup.",
            "Requests are spaced by NVD_MIN_INTERVAL_SECONDS. Confirm current NVD rate limits in the official documentation.",
        ],
        "attribution": "CVE records are retrieved from NVD when a lookup or status check runs. CryptoGuard does not bundle NVD data. Confirm current terms at https://nvd.nist.gov/.",
        "license_note": "See the NVD website for the terms that apply to its data and API. This project does not restate a license that was not copied from an official NVD page into the local documentation.",
        "data_is_downloaded": False,
    },
    {
        "id": "cyclonedx",
        "name": "CycloneDX",
        "website": "https://cyclonedx.org/",
        "documentation_url": "https://cyclonedx.org/docs/1.7/json/",
        "endpoint": "https://cyclonedx.org/schema/bom-1.7.schema.json",
        "category": "SBOM specification and schema",
        "purpose": "Define the JSON shape of a software bill of materials and validate SBOM documents CryptoGuard generates.",
        "access_method": "The official JSON Schema is vendored for offline validation. A status check requests the published schema URL.",
        "fields_used": ["bomFormat", "specVersion", "serialNumber", "version", "metadata", "components", "purl", "scope"],
        "limitations": [
            "CycloneDX is a specification and schema, not a vulnerability database.",
            "A reachable schema URL is not a security result.",
            "CryptoGuard emits CycloneDX 1.7 JSON and validates it with the vendored 1.7 schema.",
        ],
        "attribution": "The vendored file backend/app/data/bom-1.7.schema.json is the CycloneDX JSON Schema published at the official schema URL.",
        "license_note": "The schema document states: CycloneDX JSON schema is published under the terms of the Apache License 2.0.",
        "data_is_downloaded": False,
    },
]


def _latest_checks(db: Session) -> dict[str, DataSourceCheck]:
    found: dict[str, DataSourceCheck] = {}
    rows = db.query(DataSourceCheck).order_by(DataSourceCheck.checked_at.desc()).all()
    for row in rows:
        if row.source_name not in found:
            found[row.source_name] = row
    return found


def _public_check(row: DataSourceCheck | None) -> dict:
    if row is None:
        return {
            "status": "NOT CHECKED",
            "checked_at": None,
            "latency_ms": None,
            "error_category": None,
            "detail": "This source has not been checked in this database.",
        }
    return {
        "status": row.status,
        "checked_at": isoformat_utc(row.checked_at),
        "latency_ms": row.latency_ms,
        "error_category": row.error_category,
        "detail": row.detail,
    }


def list_sources(db: Session) -> dict:
    settings = get_settings()
    checks = _latest_checks(db)
    sources = []
    for item in CATALOG:
        entry = dict(item)
        entry.update(_public_check(checks.get(item["id"])))
        sources.append(entry)
    return {
        "product": "CryptoGuard",
        "nvd_enabled": settings.nvd_enabled,
        "nvd_key_configured": settings.nvd_key_configured,
        "cache_ttl_seconds": settings.vuln_cache_ttl_seconds,
        "note": "Source availability is a connectivity result. It is not evidence that software is safe or unsafe.",
        "sources": sources,
    }


def _save_check(db: Session, source_name: str, status: str, started: float, error_category: str | None, detail: str) -> dict:
    row = DataSourceCheck(
        source_name=source_name,
        status=status,
        checked_at=utcnow(),
        latency_ms=int((time.perf_counter() - started) * 1000),
        error_category=error_category,
        detail=detail[:300],
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": source_name, **_public_check(row)}


async def check_osv(db: Session) -> dict:
    settings = get_settings()
    started = time.perf_counter()
    payload = {
        "package": {"name": "lodash", "ecosystem": "npm"},
        "version": "0.0.0-cryptoguard-healthcheck",
    }
    try:
        async with http_client(settings.source_check_timeout_seconds) as client:
            response = await client.post(settings.osv_query_url, json=payload)
        if response.status_code != 200:
            return _save_check(db, "osv", "UNAVAILABLE", started, "http_error", f"OSV returned HTTP {response.status_code}.")
        body = response.json()
        if not isinstance(body, dict):
            return _save_check(db, "osv", "DEGRADED", started, "invalid_response", "OSV responded, but the body was not a JSON object.")
        return _save_check(
            db,
            "osv",
            "AVAILABLE",
            started,
            None,
            "OSV accepted a bounded package query. This check does not judge the security of any package.",
        )
    except httpx.TimeoutException:
        return _save_check(db, "osv", "UNAVAILABLE", started, "timeout", "The OSV health query timed out.")
    except (httpx.HTTPError, ValueError):
        return _save_check(db, "osv", "UNAVAILABLE", started, "network", "The OSV health query failed.")


async def check_nvd(db: Session) -> dict:
    settings = get_settings()
    started = time.perf_counter()
    headers = {}
    if settings.nvd_key_configured:
        headers["apiKey"] = settings.nvd_api_key.strip()
    try:
        async with http_client(settings.source_check_timeout_seconds) as client:
            response = await client.get(settings.nvd_api_url, params={"resultsPerPage": 1}, headers=headers)
        if response.status_code == 429:
            return _save_check(db, "nvd", "DEGRADED", started, "rate_limit", "NVD responded with HTTP 429.")
        if response.status_code != 200:
            return _save_check(db, "nvd", "UNAVAILABLE", started, "http_error", f"NVD returned HTTP {response.status_code}.")
        body = response.json()
        if not isinstance(body, dict):
            return _save_check(db, "nvd", "DEGRADED", started, "invalid_response", "NVD responded, but the body was not a JSON object.")
        return _save_check(
            db,
            "nvd",
            "AVAILABLE",
            started,
            None,
            "NVD answered a one-record pagination request. Returned CVEs are not stored as findings.",
        )
    except httpx.TimeoutException:
        return _save_check(db, "nvd", "UNAVAILABLE", started, "timeout", "The NVD status request timed out.")
    except (httpx.HTTPError, ValueError):
        return _save_check(db, "nvd", "UNAVAILABLE", started, "network", "The NVD status request failed.")


async def check_cyclonedx(db: Session) -> dict:
    settings = get_settings()
    started = time.perf_counter()
    try:
        async with http_client(settings.source_check_timeout_seconds) as client:
            async with client.stream("GET", settings.cyclonedx_schema_url) as response:
                status_code = response.status_code
                snippet = b""
                async for chunk in response.aiter_bytes():
                    snippet += chunk
                    if len(snippet) >= 64:
                        break
        if status_code != 200:
            return _save_check(db, "cyclonedx", "UNAVAILABLE", started, "http_error", f"Schema URL returned HTTP {status_code}.")
        if not snippet.lstrip().startswith(b"{"):
            return _save_check(db, "cyclonedx", "DEGRADED", started, "invalid_response", "Schema URL responded, but the body did not look like JSON.")
        return _save_check(
            db,
            "cyclonedx",
            "AVAILABLE",
            started,
            None,
            "The published CycloneDX 1.7 schema URL responded. This is not a vulnerability result.",
        )
    except httpx.TimeoutException:
        return _save_check(db, "cyclonedx", "UNAVAILABLE", started, "timeout", "The CycloneDX schema request timed out.")
    except httpx.HTTPError:
        return _save_check(db, "cyclonedx", "UNAVAILABLE", started, "network", "The CycloneDX schema request failed.")


CHECKERS = {"osv": check_osv, "nvd": check_nvd, "cyclonedx": check_cyclonedx}


async def check_sources(db: Session, selected: list[str] | None) -> dict:
    names = list(SOURCE_IDS if not selected else selected)
    unknown = [name for name in names if name not in CHECKERS]
    if unknown:
        raise ValueError("Unknown sources: " + ", ".join(unknown))
    results = []
    for name in names:
        results.append(await CHECKERS[name](db))
    return {
        "note": "These statuses describe whether a source responded. They are not security verdicts.",
        "results": results,
    }
