"""Local records for verification history, vulnerability cache, and source checks."""

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base


class VerificationRecord(Base):
    __tablename__ = "verification_records"
    __table_args__ = (
        Index("ix_verification_type_status", "operation_type", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    operation_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    algorithm: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    sanitized_metadata: Mapped[dict] = mapped_column(JSON, default=dict)


class VulnerabilityLookupCache(Base):
    __tablename__ = "vulnerability_lookup_cache"
    __table_args__ = (
        UniqueConstraint(
            "source",
            "package_name",
            "ecosystem",
            "version",
            name="uq_vuln_cache_identity",
        ),
        Index("ix_vuln_cache_expires", "expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(32), index=True)
    package_name: Mapped[str] = mapped_column(String(255))
    ecosystem: Mapped[str] = mapped_column(String(32))
    version: Mapped[str] = mapped_column(String(255))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    response_json: Mapped[dict] = mapped_column(JSON, default=dict)


class DataSourceCheck(Base):
    __tablename__ = "data_source_checks"
    __table_args__ = (Index("ix_source_checked", "source_name", "checked_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32))
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
