"""Combine manifest parsing with OSV and optional NVD lookups."""

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import NO_MATCH_MESSAGE
from app.services.manifest import ParsedComponent, ParsedManifest
from app.services.nvd import lookup_cve, validate_cve_id
from app.services.osv import lookup_package


def _component_row(component: ParsedComponent, extra: dict) -> dict:
    row = component.as_dict()
    row.update(extra)
    return row


def _trim_finding(advisory: dict, component: ParsedComponent) -> dict:
    return {
        "id": advisory.get("canonical_id") or advisory.get("id"),
        "advisory_id": advisory.get("id"),
        "source": advisory.get("source", "osv"),
        "package": component.queried_name,
        "version": component.queried_version,
        "summary": (advisory.get("summary") or "")[:300],
        "modified": advisory.get("modified"),
        "reference_url": advisory.get("reference_url") or advisory.get("osv_url"),
        "aliases": (advisory.get("aliases") or [])[:10],
        "severity": (advisory.get("severity") or [])[:3],
        "severity_label": advisory.get("severity_label"),
    }


async def analyze_manifest(db: Session, parsed: ParsedManifest, *, refresh: bool, include_nvd: bool) -> dict:
    settings = get_settings()
    memo: dict = {}
    components = []
    advisory_ids: list[str] = []
    findings: list[dict] = []
    queried = 0
    errors = 0
    cve_ids: list[str] = []

    for component in parsed.components:
        if not component.queried_version:
            components.append(
                _component_row(
                    component,
                    {
                        "query_status": "skipped",
                        "cached": False,
                        "retrieved_at": None,
                        "advisories": [],
                        "message": component.warning,
                        "source": None,
                        "truncated": False,
                    },
                )
            )
            continue
        if queried >= settings.max_packages_per_scan:
            components.append(
                _component_row(
                    component,
                    {
                        "query_status": "skipped",
                        "cached": False,
                        "retrieved_at": None,
                        "advisories": [],
                        "message": "The live query limit for this request was reached. Narrow the manifest or raise MAX_PACKAGES_PER_SCAN.",
                        "source": None,
                        "truncated": False,
                    },
                )
            )
            continue
        queried += 1
        live = await lookup_package(
            db,
            name=component.queried_name,
            ecosystem=component.ecosystem,
            version=component.queried_version,
            refresh=refresh,
            memo=memo,
        )
        if live["query_status"] == "error":
            errors += 1
        else:
            for advisory in live["advisories"]:
                canonical = advisory.get("canonical_id") or advisory.get("id")
                if canonical and canonical not in advisory_ids:
                    advisory_ids.append(canonical)
                if len(findings) < 100:
                    findings.append(_trim_finding(advisory, component))
                for alias in advisory.get("aliases") or []:
                    if isinstance(alias, str) and alias.startswith("CVE-") and alias not in cve_ids:
                        cve_ids.append(alias)
                if isinstance(advisory.get("id"), str) and advisory["id"].startswith("CVE-") and advisory["id"] not in cve_ids:
                    cve_ids.append(advisory["id"])
        components.append(_component_row(component, live))

    nvd = await _maybe_nvd(db, cve_ids, include_nvd=include_nvd, refresh=refresh)
    for record in nvd["records"]:
        cve_id = record.get("id")
        if cve_id and cve_id not in advisory_ids:
            advisory_ids.append(cve_id)
            if len(findings) < 100:
                findings.append(
                    {
                        "id": cve_id,
                        "advisory_id": cve_id,
                        "source": "nvd",
                        "package": None,
                        "version": None,
                        "summary": (record.get("summary") or "")[:300],
                        "modified": record.get("modified"),
                        "reference_url": record.get("reference_url") or record.get("nvd_url"),
                        "aliases": [],
                    }
                )

    return {
        "manifest_format": parsed.manifest_format,
        "subject_name": parsed.subject_name,
        "subject_version": parsed.subject_version,
        "components": components,
        "warnings": parsed.warnings,
        "advisory_ids": advisory_ids,
        "findings": findings,
        "queried_count": queried,
        "skipped_count": len(parsed.components) - queried,
        "source_errors": errors,
        "nvd": nvd,
        "no_match_meaning": NO_MATCH_MESSAGE,
    }


async def query_one(
    db: Session,
    *,
    name: str,
    ecosystem: str,
    version: str,
    refresh: bool,
    include_nvd: bool,
) -> dict:
    if ecosystem not in {"npm", "PyPI"}:
        raise ValueError("Ecosystem must be npm or PyPI.")
    if not name.strip() or not version.strip():
        raise ValueError("Package name and version are required.")
    if ecosystem == "npm" and any(token in version for token in "^~><=* xX"):
        raise ValueError("Version ranges are not sent to OSV. Provide an exact version.")
    live = await lookup_package(
        db,
        name=name.strip(),
        ecosystem=ecosystem,
        version=version.strip(),
        refresh=refresh,
    )
    cve_ids: list[str] = []
    advisory_ids: list[str] = []
    if live["query_status"] == "ok":
        for advisory in live["advisories"]:
            canonical = advisory.get("canonical_id") or advisory.get("id")
            if canonical and canonical not in advisory_ids:
                advisory_ids.append(canonical)
            for alias in advisory.get("aliases") or []:
                if isinstance(alias, str) and alias.startswith("CVE-") and alias not in cve_ids:
                    cve_ids.append(alias)
    nvd = await _maybe_nvd(db, cve_ids, include_nvd=include_nvd, refresh=refresh)
    for record in nvd["records"]:
        if record.get("id") and record["id"] not in advisory_ids:
            advisory_ids.append(record["id"])
    return {
        "package": {"name": name.strip(), "ecosystem": ecosystem, "version": version.strip()},
        "osv": live,
        "nvd": nvd,
        "advisory_ids": advisory_ids,
        "no_match_meaning": NO_MATCH_MESSAGE,
    }


async def query_cve(db: Session, cve_id: str, refresh: bool) -> dict:
    normalized = validate_cve_id(cve_id)
    result = await lookup_cve(db, normalized, refresh=refresh)
    advisory_ids = []
    if result.get("record") and result["record"].get("id"):
        advisory_ids.append(result["record"]["id"])
    return {"cve_id": normalized, "nvd": result, "advisory_ids": advisory_ids}


async def _maybe_nvd(db: Session, cve_ids: list[str], *, include_nvd: bool, refresh: bool) -> dict:
    if not include_nvd:
        return {"status": "not_requested", "records": [], "errors": [], "message": "NVD was not requested."}
    settings = get_settings()
    if not settings.nvd_enabled:
        return {
            "status": "disabled",
            "records": [],
            "errors": [],
            "message": "NVD lookups are disabled. OSV results above are unaffected.",
        }
    if not cve_ids:
        return {
            "status": "no_cve_alias",
            "records": [],
            "errors": [],
            "message": "OSV did not provide a CVE identifier to look up in NVD.",
        }
    selected = cve_ids[: settings.nvd_max_cves_per_query]
    records = []
    errors = []
    for cve_id in selected:
        result = await lookup_cve(db, cve_id, refresh=refresh)
        if result.get("record"):
            records.append(result["record"])
        elif result["query_status"] != "ok":
            errors.append({"id": cve_id, "message": result["message"]})
    message = None
    if len(cve_ids) > len(selected):
        message = f"Only the first {len(selected)} CVE identifiers were sent to NVD."
    return {"status": "queried", "records": records, "errors": errors, "message": message}
