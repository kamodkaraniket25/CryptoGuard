"""Canonical provenance records and their verification rules."""

import json

from app.core.constants import CANONICALIZATION_RULE
from app.utils.security import normalize_sha256

CANONICAL_FIELDS = (
    "artifact_sha256",
    "builder_id",
    "build_timestamp",
    "source_repository",
    "source_revision",
)
FIELD_LIMITS = {
    "artifact_sha256": 80,
    "builder_id": 200,
    "build_timestamp": 100,
    "source_repository": 500,
    "source_revision": 200,
}


def canonical_payload(record: dict) -> dict:
    if not isinstance(record, dict):
        raise ValueError("Provenance record must be a JSON object.")
    payload: dict[str, str] = {}
    missing: list[str] = []
    for field in CANONICAL_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            missing.append(field)
            continue
        text = value.strip()
        if len(text) > FIELD_LIMITS[field]:
            raise ValueError(f"{field} is too long.")
        payload[field] = text
    if missing:
        raise ValueError("Missing required provenance fields: " + ", ".join(missing))
    payload["artifact_sha256"] = normalize_sha256(payload["artifact_sha256"])
    return {key: payload[key] for key in sorted(payload)}


def canonical_bytes(record: dict) -> bytes:
    return json.dumps(
        canonical_payload(record),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_text(record: dict) -> str:
    return canonical_bytes(record).decode("utf-8")


def describe_canonicalization() -> str:
    return CANONICALIZATION_RULE
