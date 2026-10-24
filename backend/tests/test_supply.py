"""Provenance, manifest, SBOM, cache, and source-status tests."""

import json

import httpx

from app.services.http_client import set_transport
from app.services.manifest import parse_manifest
from app.services.osv import parse_vulnerability
from app.services.sbom import generate_sbom, validate_sbom
from app.core.constants import NO_MATCH_MESSAGE


PACKAGE_JSON = json.dumps(
    {
        "name": "demo-app",
        "version": "1.2.3",
        "dependencies": {"left-pad": "1.0.0", "react": "^18.3.1"},
        "devDependencies": {"typescript": "5.4.5"},
        "optionalDependencies": {"fsevents": "2.3.3"},
    }
)

REQUIREMENTS = """
# classroom sample
requests==2.31.0
Flask>=2.0
# no version
rich
-e git+https://example.com/project.git
"""


def test_osv_severity_is_copied_only_when_present():
    reported = parse_vulnerability(
        {
            "id": "GHSA-1",
            "severity": [{"type": "CVSS_V3", "score": "CVSS:3.1/AV:N"}],
            "database_specific": {"severity": "HIGH"},
        }
    )
    assert reported["severity_label"] == "HIGH"
    assert reported["severity"] == [{"type": "CVSS_V3", "score": "CVSS:3.1/AV:N"}]
    absent = parse_vulnerability({"id": "GHSA-2", "summary": "No score"})
    assert absent["severity"] == []
    assert absent["severity_label"] is None


def test_manifest_parsing_distinguishes_exact_versions():
    npm = parse_manifest("package.json", PACKAGE_JSON)
    by_name = {item.name: item for item in npm.components}
    assert by_name["left-pad"].version_status == "exact"
    assert by_name["left-pad"].ecosystem == "npm"
    assert by_name["react"].version_status == "range"
    assert by_name["react"].queried_version is None
    assert by_name["typescript"].scope == "excluded"
    assert by_name["fsevents"].scope == "optional"
    assert npm.subject_name == "demo-app"

    python = parse_manifest("requirements.txt", REQUIREMENTS)
    by_name = {item.name: item for item in python.components}
    assert by_name["requests"].queried_name == "requests"
    assert by_name["requests"].queried_version == "2.31.0"
    assert by_name["Flask"].queried_name == "flask"
    assert by_name["Flask"].version_status == "range"
    assert by_name["rich"].version_status == "missing"
    assert any("editable" in warning or "URL" in warning for warning in python.warnings)


def test_sbom_validates_against_cyclonedx_17_schema():
    parsed = parse_manifest("package.json", PACKAGE_JSON)
    document = generate_sbom(parsed)
    errors = validate_sbom(document)
    assert errors == []
    assert document["bomFormat"] == "CycloneDX"
    assert document["specVersion"] == "1.7"
    names = {item["name"] for item in document["components"]}
    assert "left-pad" in names
    react = next(item for item in document["components"] if item["name"] == "react")
    assert "version" not in react
    assert "licenses" not in document
    assert "dependencies" not in document
    left_pad = next(item for item in document["components"] if item["name"] == "left-pad")
    assert left_pad["purl"] == "pkg:npm/left-pad@1.0.0"
    assert left_pad["version"] == "1.0.0"


def test_invalid_manifest(api_client):
    client, _database = api_client
    response = client.post(
        "/api/dependencies/scan",
        files={"file": ("package.json", b"{not json")},
    )
    assert response.status_code == 400


def _osv_transport(counter: dict | None = None, mode: str = "hit"):
    def handler(request: httpx.Request) -> httpx.Response:
        if counter is not None:
            counter["n"] = counter.get("n", 0) + 1
        if mode == "timeout":
            raise httpx.TimeoutException("timed out")
        if mode == "http":
            return httpx.Response(503, json={"error": "unavailable"})
        if "healthcheck" in request.content.decode():
            return httpx.Response(200, json={"vulns": []})
        if request.url.host == "services.nvd.nist.gov":
            return httpx.Response(200, json={"resultsPerPage": 1, "totalResults": 1, "vulnerabilities": []})
        if request.url.host == "cyclonedx.org":
            return httpx.Response(200, content=b'{"bomFormat":"CycloneDX"}')
        return httpx.Response(
            200,
            json={
                "vulns": [
                    {
                        "id": "GHSA-test-0000-0000",
                        "summary": "Example advisory used by a mocked OSV response.",
                        "modified": "2024-05-01T00:00:00Z",
                        "published": "2024-04-01T00:00:00Z",
                        "aliases": ["CVE-2024-9999"],
                        "severity": [{"type": "CVSS_V3", "score": "CVSS:3.1/AV:N/AC:L"}],
                        "database_specific": {"severity": "HIGH"},
                        "references": [{"type": "WEB", "url": "https://example.com/advisory"}],
                        "affected": [
                            {
                                "package": {"name": "left-pad", "ecosystem": "npm"},
                                "versions": ["1.0.0"],
                            }
                        ],
                    }
                ]
            },
        )

    return httpx.MockTransport(handler)


def test_dependency_scan_uses_osv_and_skips_ranges(api_client):
    client, _database = api_client
    set_transport(_osv_transport())
    response = client.post("/api/dependencies/scan", files={"file": ("package.json", PACKAGE_JSON.encode())})
    assert response.status_code == 200
    body = response.json()
    components = {item["name"]: item for item in body["result"]["components"]}
    assert components["left-pad"]["query_status"] == "ok"
    assert components["left-pad"]["advisories"][0]["id"] == "GHSA-test-0000-0000"
    assert components["left-pad"]["advisories"][0]["severity_label"] == "HIGH"
    assert components["left-pad"]["advisories"][0]["severity"][0]["score"] == "CVSS:3.1/AV:N/AC:L"
    assert components["react"]["query_status"] == "skipped"
    assert "CVE-2024-9999" in body["result"]["advisory_ids"]
    set_transport(None)


def test_osv_empty_result_is_not_called_safe(api_client):
    client, _database = api_client

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    set_transport(httpx.MockTransport(handler))
    response = client.post(
        "/api/vulnerabilities/query",
        json={"name": "left-pad", "ecosystem": "npm", "version": "9.9.9"},
    )
    assert response.status_code == 200
    assert response.json()["result"]["osv"]["message"] == NO_MATCH_MESSAGE
    set_transport(None)


def test_osv_timeout_and_cache(api_client):
    client, _database = api_client
    calls = {"n": 0}
    set_transport(_osv_transport(calls))
    first = client.post(
        "/api/vulnerabilities/query",
        json={"name": "left-pad", "ecosystem": "npm", "version": "1.0.0"},
    )
    second = client.post(
        "/api/vulnerabilities/query",
        json={"name": "left-pad", "ecosystem": "npm", "version": "1.0.0"},
    )
    assert first.status_code == 200
    assert calls["n"] == 1
    assert second.json()["result"]["osv"]["cached"] is True
    refreshed = client.post(
        "/api/vulnerabilities/query",
        json={"name": "left-pad", "ecosystem": "npm", "version": "1.0.0", "refresh": True},
    )
    assert refreshed.json()["result"]["osv"]["cached"] is False
    assert calls["n"] == 2
    cleared = client.delete("/api/vulnerabilities/cache")
    assert cleared.json()["deleted"] >= 1

    set_transport(_osv_transport(mode="timeout"))
    timed_out = client.post(
        "/api/vulnerabilities/query",
        json={"name": "missing", "ecosystem": "npm", "version": "1.0.0"},
    )
    assert timed_out.status_code == 200
    assert timed_out.json()["result"]["osv"]["query_status"] == "error"
    assert "does not mean" in timed_out.json()["result"]["osv"]["message"]
    set_transport(None)


def test_source_status_check(api_client):
    client, _database = api_client
    before = client.get("/api/sources")
    assert before.status_code == 200
    names = {item["name"] for item in before.json()["sources"]}
    assert "OSV Vulnerability Database" in names
    assert "National Vulnerability Database (NVD)" in names
    assert "CycloneDX" in names
    assert all(item["status"] == "NOT CHECKED" for item in before.json()["sources"])

    set_transport(_osv_transport())
    checked = client.post("/api/sources/check", json={"sources": ["osv", "nvd", "cyclonedx"]})
    assert checked.status_code == 200
    statuses = {item["id"]: item["status"] for item in checked.json()["results"]}
    assert statuses == {"osv": "AVAILABLE", "nvd": "AVAILABLE", "cyclonedx": "AVAILABLE"}
    set_transport(None)


def test_provenance_missing_digest_and_signature(api_client):
    client, _database = api_client
    incomplete = {"artifact_sha256": "abcd", "source_repository": "https://example.com/repo"}
    response = client.post("/api/provenance/verify", data={"record_json": json.dumps(incomplete)})
    assert response.status_code == 200
    body = response.json()["result"]
    assert body["record_status"] == "INCOMPLETE_RECORD"
    assert body["digest_status"] == "NOT_VERIFIED"
    assert body["signature_status"] == "NOT_VERIFIED"
    assert "signature" in body["missing_evidence"]

    digest = "a" * 64
    record = {
        "artifact_sha256": digest,
        "source_repository": "https://example.com/repo",
        "source_revision": "abc123",
        "builder_id": "builder-1",
        "build_timestamp": "2026-10-17T00:00:00Z",
    }
    mismatch = client.post(
        "/api/provenance/verify",
        data={"record_json": json.dumps(record)},
        files={"artifact": ("app.bin", b"bytes")},
    )
    assert mismatch.json()["result"]["digest_status"] == "DIGEST_MISMATCH"
    assert mismatch.json()["result"]["signature_status"] == "NOT_VERIFIED"


def test_signed_provenance_matches_artifact(api_client):
    client, _database = api_client
    artifact = b"artifact-bytes"
    import hashlib

    digest = hashlib.sha256(artifact).hexdigest()
    record = {
        "artifact_sha256": digest,
        "source_repository": "https://example.com/repo.git",
        "source_revision": "def456",
        "builder_id": "local-builder",
        "build_timestamp": "2026-10-17T12:00:00Z",
    }
    keys = client.post("/api/signatures/keygen")
    private_key = keys.json()["result"]["private_key_pem"]
    public_key = keys.json()["result"]["public_key_pem"]
    signed = client.post("/api/provenance/sign", json={"record": record, "private_key_pem": private_key})
    assert signed.status_code == 200
    record["signature"] = signed.json()["result"]["signature"]
    verified = client.post(
        "/api/provenance/verify",
        data={"record_json": json.dumps(record), "public_key_pem": public_key},
        files={"artifact": ("app.bin", artifact)},
    )
    result = verified.json()["result"]
    assert result["digest_status"] == "DIGEST_MATCH"
    assert result["signature_status"] == "SIGNATURE_VALID"
    assert verified.json()["status"] == "success"
    raw = _database.read_bytes() if False else None
    database = api_client[1]
    assert b"BEGIN PRIVATE KEY" not in database.read_bytes()
    assert private_key.encode() not in database.read_bytes()
    assert raw is None
