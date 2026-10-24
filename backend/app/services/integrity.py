"""SHA-256 file integrity."""

import time

from sqlalchemy.orm import Session

from app.core.constants import LIMITATIONS, Op, Status
from app.services.records import envelope
from app.utils.security import digests_match, normalize_sha256


def hash_result(
    db: Session,
    *,
    started: float,
    file_name: str,
    file_size: int,
    digest: str,
    reference: str | None,
) -> dict:
    if reference is None:
        verdict = "NOT VERIFIED"
        status = Status.NOT_VERIFIED
        operation = Op.HASH
        limitations = LIMITATIONS[Op.HASH]
        metadata = {"verdict": verdict, "reference_supplied": False}
    else:
        normalized = normalize_sha256(reference)
        matched = digests_match(digest, normalized)
        verdict = "MATCH" if matched else "MISMATCH"
        status = Status.SUCCESS if matched else Status.FAILED
        operation = Op.HASH_VERIFY
        limitations = LIMITATIONS[Op.HASH_VERIFY]
        metadata = {"verdict": verdict, "reference_supplied": True}
    return envelope(
        db,
        operation_type=operation,
        status=status,
        algorithm="SHA-256",
        started=started,
        result={
            "verdict": verdict,
            "file_name": file_name,
            "file_size": file_size,
            "sha256": digest,
            "reference_supplied": reference is not None,
        },
        limitations=limitations,
        metadata=metadata,
        file_name=file_name,
        file_size=file_size,
        sha256_digest=digest,
    )


def start_timer() -> float:
    return time.perf_counter()
