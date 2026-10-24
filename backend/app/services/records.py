"""Persist sanitized verification history. Secrets are never passed into this module."""

import time
import uuid

from sqlalchemy.orm import Session

from app.core.constants import FULL_TITLE, PRODUCT_NAME
from app.models.tables import VerificationRecord
from app.utils.timeutil import isoformat_utc, utcnow


def save_operation(
    db: Session,
    *,
    operation_type: str,
    status: str,
    algorithm: str | None,
    duration_ms: int,
    file_name: str | None = None,
    file_size: int | None = None,
    sha256_digest: str | None = None,
    metadata: dict | None = None,
) -> VerificationRecord:
    record = VerificationRecord(
        operation_id=str(uuid.uuid4()),
        operation_type=operation_type,
        status=status,
        algorithm=algorithm,
        file_name=file_name,
        file_size=file_size,
        sha256_digest=sha256_digest,
        created_at=utcnow(),
        duration_ms=max(duration_ms, 0),
        sanitized_metadata=metadata or {},
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def envelope(
    db: Session,
    *,
    operation_type: str,
    status: str,
    algorithm: str | None,
    started: float,
    result: dict,
    limitations: list[str],
    metadata: dict | None = None,
    file_name: str | None = None,
    file_size: int | None = None,
    sha256_digest: str | None = None,
) -> dict:
    duration_ms = int((time.perf_counter() - started) * 1000)
    record = save_operation(
        db,
        operation_type=operation_type,
        status=status,
        algorithm=algorithm,
        duration_ms=duration_ms,
        file_name=file_name,
        file_size=file_size,
        sha256_digest=sha256_digest,
        metadata=metadata,
    )
    return {
        "product": PRODUCT_NAME,
        "full_title": FULL_TITLE,
        "operation_id": record.operation_id,
        "operation_type": record.operation_type,
        "status": record.status,
        "algorithm": record.algorithm,
        "created_at": isoformat_utc(record.created_at),
        "duration_ms": record.duration_ms,
        "result": result,
        "limitations": limitations,
    }
