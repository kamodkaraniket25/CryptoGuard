"""Runtime configuration loaded from the environment and an optional .env file."""

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
APP_VERSION = "1.0.0"
PRODUCT_NAME = "CryptoGuard"
FULL_TITLE = (
    "CryptoGuard — Cryptographic Integrity and Software Supply Chain Verification Platform"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = PRODUCT_NAME
    app_version: str = APP_VERSION
    database_url: str = "sqlite:////tmp/cryptoguard.db" if os.getenv("VERCEL") else "sqlite:///./data/cryptoguard.db"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    max_upload_bytes: int = 4 * 1024 * 1024 if os.getenv("VERCEL") else 10 * 1024 * 1024
    chunk_size: int = 64 * 1024
    osv_query_url: str = "https://api.osv.dev/v1/query"
    osv_timeout_seconds: float = 20.0
    osv_max_pages: int = 3
    vuln_cache_ttl_seconds: int = 6 * 3600
    max_packages_per_scan: int = 40
    max_components: int = 500
    nvd_api_url: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    nvd_api_key: str = ""
    nvd_enabled: bool = False
    nvd_timeout_seconds: float = 20.0
    nvd_min_interval_seconds: float = 6.0
    nvd_max_cves_per_query: int = 3
    cyclonedx_spec_version: str = "1.7"
    cyclonedx_schema_url: str = "https://cyclonedx.org/schema/bom-1.7.schema.json"
    source_check_timeout_seconds: float = 15.0
    json_body_limit_bytes: int = 1_000_000

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def nvd_key_configured(self) -> bool:
        return bool(self.nvd_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()


def resolve_database_url(url: str) -> str:
    """Resolve a relative SQLite path against the backend directory."""
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return url
    raw = url[len(prefix) :]
    if raw in {":memory:", ""} or raw.startswith("file:"):
        return url
    path = Path(raw)
    if not path.is_absolute():
        path = (BACKEND_ROOT / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return prefix + path.as_posix()
