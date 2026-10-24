"""Verification history queries, reports, and CSV export."""

import csv
from datetime import datetime, time, timedelta, timezone
from io import StringIO

from sqlalchemy.orm import Session

from app.core.constants import FULL_TITLE, LIMITATIONS, PRODUCT_NAME
from app.models.tables import VerificationRecord
from app.utils.timeutil import isoformat_utc


def _start(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        day = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Dates must use YYYY-MM-DD.") from exc
    return datetime.combine(day, time.min, tzinfo=timezone.utc)


def _end(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        day = datetime.strptime(value, "%Y-%m-%d").date() + timedelta(days=1)
    except ValueError as exc:
        raise ValueError("Dates must use YYYY-MM-DD.") from exc
    return datetime.combine(day, time.min, tzinfo=timezone.utc)


def _query(db: Session, operation_type: str | None, status: str | None, date_from: str | None, date_to: str | None):
    query = db.query(VerificationRecord)
    if operation_type:
        query = query.filter(VerificationRecord.operation_type == operation_type)
    if status:
        query = query.filter(VerificationRecord.status == status)
    start = _start(date_from)
    end = _end(date_to)
    if start:
        query = query.filter(VerificationRecord.created_at >= start)
    if end:
        query = query.filter(VerificationRecord.created_at < end)
    return query


def summary(row: VerificationRecord) -> dict:
    metadata = row.sanitized_metadata or {}
    return {
        "operation_id": row.operation_id,
        "operation_type": row.operation_type,
        "status": row.status,
        "algorithm": row.algorithm,
        "file_name": row.file_name,
        "file_size": row.file_size,
        "sha256_digest": row.sha256_digest,
        "created_at": isoformat_utc(row.created_at),
        "duration_ms": row.duration_ms,
        "verdict": metadata.get("verdict") or metadata.get("digest_status") or metadata.get("record_status"),
    }


def detail(row: VerificationRecord) -> dict:
    body = summary(row)
    body["product"] = PRODUCT_NAME
    body["full_title"] = FULL_TITLE
    body["metadata"] = row.sanitized_metadata or {}
    body["limitations"] = LIMITATIONS.get(row.operation_type, [])
    return body


def list_history(
    db: Session,
    *,
    operation_type: str | None,
    status: str | None,
    date_from: str | None,
    date_to: str | None,
    limit: int,
    offset: int,
) -> dict:
    query = _query(db, operation_type, status, date_from, date_to)
    total = query.count()
    rows = query.order_by(VerificationRecord.created_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "limit": limit, "offset": offset, "items": [summary(row) for row in rows]}


def get_history(db: Session, operation_id: str) -> VerificationRecord | None:
    return db.query(VerificationRecord).filter_by(operation_id=operation_id).one_or_none()


def delete_history(db: Session, operation_id: str) -> bool:
    row = get_history(db, operation_id)
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def export_csv(
    db: Session,
    *,
    operation_type: str | None,
    status: str | None,
    date_from: str | None,
    date_to: str | None,
) -> str:
    rows = _query(db, operation_type, status, date_from, date_to).order_by(VerificationRecord.created_at.desc()).all()
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "product",
            "operation_id",
            "created_at",
            "operation_type",
            "status",
            "algorithm",
            "file_name",
            "file_size",
            "sha256_digest",
            "duration_ms",
            "advisory_ids",
        ]
    )
    for row in rows:
        metadata = row.sanitized_metadata or {}
        identifiers = metadata.get("advisory_ids") if isinstance(metadata.get("advisory_ids"), list) else []
        writer.writerow(
            [
                PRODUCT_NAME,
                row.operation_id,
                isoformat_utc(row.created_at),
                row.operation_type,
                row.status,
                row.algorithm or "",
                row.file_name or "",
                row.file_size if row.file_size is not None else "",
                row.sha256_digest or "",
                row.duration_ms,
                " ".join(str(item) for item in identifiers),
            ]
        )
    return buffer.getvalue()
