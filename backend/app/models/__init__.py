"""ORM models. Importing this module registers every table."""

from app.models.tables import DataSourceCheck, VerificationRecord, VulnerabilityLookupCache

__all__ = [
    "DataSourceCheck",
    "VerificationRecord",
    "VulnerabilityLookupCache",
]
