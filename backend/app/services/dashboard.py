"""Dashboard aggregates from local verification records and source checks."""

from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session

from app.core.constants import Op
from app.models.tables import VerificationRecord
from app.services.sources import list_sources
from app.utils.timeutil import as_utc, isoformat_utc, utcnow


def _count(db: Session, operation_type: str, status: str | None = None) -> int:
    query = db.query(VerificationRecord).filter(VerificationRecord.operation_type == operation_type)
    if status is not None:
        query = query.filter(VerificationRecord.status == status)
    return query.count()


def _activity(db: Session) -> list[dict]:
    today = utcnow().date()
    start_day = today - timedelta(days=13)
    start = datetime.combine(start_day, time.min, tzinfo=utcnow().tzinfo)
    rows = db.query(VerificationRecord).filter(VerificationRecord.created_at >= start).all()
    counts = {(start_day + timedelta(days=offset)).isoformat(): 0 for offset in range(14)}
    for row in rows:
        key = as_utc(row.created_at).date().isoformat()
        if key in counts:
            counts[key] += 1
    return [{"date": day, "count": count} for day, count in counts.items()]


def _findings(db: Session) -> int:
    identifiers: set[str] = set()
    rows = (
        db.query(VerificationRecord)
        .filter(VerificationRecord.operation_type.in_([Op.DEPENDENCY_SCAN, Op.VULNERABILITY_QUERY]))
        .all()
    )
    for row in rows:
        metadata = row.sanitized_metadata or {}
        for item in metadata.get("advisory_ids") or []:
            identifiers.add(str(item))
    return len(identifiers)


def _recent(db: Session) -> list[dict]:
    rows = db.query(VerificationRecord).order_by(VerificationRecord.created_at.desc()).limit(8).all()
    return [
        {
            "operation_id": row.operation_id,
            "operation_type": row.operation_type,
            "status": row.status,
            "algorithm": row.algorithm,
            "file_name": row.file_name,
            "created_at": isoformat_utc(row.created_at),
        }
        for row in rows
    ]


def dashboard_stats(db: Session) -> dict:
    total = db.query(VerificationRecord).count()
    sources = [
        {
            "id": item["id"],
            "name": item["name"],
            "status": item["status"],
            "checked_at": item["checked_at"],
        }
        for item in list_sources(db)["sources"]
    ]
    return {
        "product": "CryptoGuard",
        "total_operations": total,
        "integrity_success": _count(db, Op.HASH_VERIFY, "success"),
        "integrity_failed": _count(db, Op.HASH_VERIFY, "failed"),
        "integrity_not_verified": _count(db, Op.HASH, "not_verified"),
        "hmac_generated": _count(db, Op.HMAC_GENERATE),
        "hmac_verified_success": _count(db, Op.HMAC_VERIFY, "success"),
        "hmac_verified_failed": _count(db, Op.HMAC_VERIFY, "failed"),
        "signatures_generated": _count(db, Op.SIGNATURE_KEYGEN) + _count(db, Op.SIGNATURE_SIGN),
        "signatures_verified_success": _count(db, Op.SIGNATURE_VERIFY, "success"),
        "signatures_verified_failed": _count(db, Op.SIGNATURE_VERIFY, "failed"),
        "provenance_checks": _count(db, Op.PROVENANCE_VERIFY),
        "dependency_scans": _count(db, Op.DEPENDENCY_SCAN),
        "vulnerability_queries": _count(db, Op.VULNERABILITY_QUERY),
        "vulnerability_findings": _findings(db),
        "sbom_generated": _count(db, Op.SBOM_GENERATE),
        "recent_operations": _recent(db),
        "activity": _activity(db),
        "sources": sources,
        "notes": [
            "Counts come from verification records stored in the local database.",
            "Vulnerability findings are unique advisory identifiers saved from OSV or NVD lookups.",
            "A source that has not been checked, or that is unavailable, is not treated as proof that no vulnerabilities exist.",
        ],
    }
