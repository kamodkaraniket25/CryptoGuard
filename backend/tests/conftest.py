"""Shared API client pointed at a temporary SQLite database."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_http_transport():
    from app.services.http_client import set_transport
    from app.services.nvd import reset_pacing

    set_transport(None)
    reset_pacing()
    yield
    set_transport(None)
    reset_pacing()


def build_client(tmp_path, monkeypatch, **env: str):
    database = tmp_path / "cryptoguard.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database.as_posix()}")
    monkeypatch.setenv("NVD_MIN_INTERVAL_SECONDS", "0")
    monkeypatch.setenv("NVD_ENABLED", "false")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.main import create_app

    application = create_app()
    client = TestClient(application)
    client.__enter__()
    return client, database


@pytest.fixture()
def api_client(tmp_path, monkeypatch):
    client, database = build_client(tmp_path, monkeypatch)
    try:
        yield client, database
    finally:
        client.__exit__(None, None, None)


@pytest.fixture()
def small_client(tmp_path, monkeypatch):
    client, database = build_client(tmp_path, monkeypatch, MAX_UPLOAD_BYTES="4")
    try:
        yield client, database
    finally:
        client.__exit__(None, None, None)
