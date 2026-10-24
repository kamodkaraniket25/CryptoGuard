"""History, dashboard, and database persistence tests."""


def test_history_export_and_delete(api_client):
    client, database = api_client
    created = client.post("/api/integrity/hash", files={"file": ("readme.txt", b"hello")})
    operation_id = created.json()["operation_id"]
    listed = client.get("/api/history")
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1
    detail = client.get(f"/api/history/{operation_id}")
    assert detail.json()["product"] == "CryptoGuard"
    assert detail.json()["sha256_digest"] == created.json()["result"]["sha256"]
    exported = client.get("/api/history/export")
    assert exported.status_code == 200
    assert "text/csv" in exported.headers["content-type"]
    assert operation_id in exported.text
    assert "CryptoGuard" in exported.text
    removed = client.delete(f"/api/history/{operation_id}")
    assert removed.json()["deleted"] is True
    missing = client.get(f"/api/history/{operation_id}")
    assert missing.status_code == 404
    assert database.exists()


def test_dashboard_uses_database_records(api_client):
    client, _database = api_client
    empty = client.get("/api/dashboard/stats")
    assert empty.json()["total_operations"] == 0
    assert empty.json()["vulnerability_findings"] == 0
    assert len(empty.json()["activity"]) == 14
    client.post("/api/integrity/hash", files={"file": ("one.txt", b"one")})
    filled = client.get("/api/dashboard/stats")
    assert filled.json()["total_operations"] == 1
    assert filled.json()["integrity_not_verified"] == 1
    assert filled.json()["recent_operations"][0]["operation_type"] == "hash"


def test_health(api_client):
    client, _database = api_client
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["product"] == "CryptoGuard"
    assert response.json()["database"] == "ok"
