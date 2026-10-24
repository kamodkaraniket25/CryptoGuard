"""Persistent cache of successful vulnerability lookups."""

from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.tables import VulnerabilityLookupCache
from app.utils.timeutil import as_utc, utcnow


def get_cached(db: Session, source: str, package_name: str, ecosystem: str, version: str) -> dict | None:
    row = (
        db.query(VulnerabilityLookupCache)
        .filter_by(source=source, package_name=package_name, ecosystem=ecosystem, version=version)
        .one_or_none()
    )
    if row is None:
        return None
    if as_utc(row.expires_at) <= utcnow():
        return None
    return {
        "retrieved_at": row.retrieved_at,
        "expires_at": row.expires_at,
        "payload": row.response_json,
    }


def store_cache(
    db: Session,
    *,
    source: str,
    package_name: str,
    ecosystem: str,
    version: str,
    payload: dict,
) -> VulnerabilityLookupCache:
    now = utcnow()
    expires = now + timedelta(seconds=get_settings().vuln_cache_ttl_seconds)
    row = (
        db.query(VulnerabilityLookupCache)
        .filter_by(source=source, package_name=package_name, ecosystem=ecosystem, version=version)
        .one_or_none()
    )
    if row is None:
        row = VulnerabilityLookupCache(
            source=source,
            package_name=package_name,
            ecosystem=ecosystem,
            version=version,
            retrieved_at=now,
            expires_at=expires,
            response_json=payload,
        )
        db.add(row)
    else:
        row.retrieved_at = now
        row.expires_at = expires
        row.response_json = payload
    db.commit()
    db.refresh(row)
    return row


def clear_cache(db: Session) -> int:
    count = db.query(VulnerabilityLookupCache).delete()
    db.commit()
    return int(count)
