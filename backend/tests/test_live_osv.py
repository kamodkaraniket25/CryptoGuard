"""Optional live OSV call. Run with CRYPTOGUARD_LIVE_API=1."""

import os

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(os.getenv("CRYPTOGUARD_LIVE_API") != "1", reason="Set CRYPTOGUARD_LIVE_API=1 to call OSV.")
def test_live_osv_query(api_client):
    client, _database = api_client
    response = client.post(
        "/api/vulnerabilities/query",
        json={"name": "lodash", "ecosystem": "npm", "version": "4.17.20", "refresh": True},
    )
    assert response.status_code == 200
    body = response.json()["result"]["osv"]
    assert body["query_status"] == "ok"
    assert body["source"] == "osv"
    assert isinstance(body["advisories"], list)
