"""Cryptographic endpoint tests."""

import hashlib

from app.services.hmac_service import compute_tag, verify_tag
from app.services.signatures import generate_keypair, sign_bytes, verify_bytes
from app.utils.security import digests_match

EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_sha256_matches_hashlib():
    digest = hashlib.sha256(b"crypto-guard").hexdigest()
    assert digests_match(digest, digest)
    assert not digests_match(digest, EMPTY_SHA256)


def test_empty_file_hash(api_client):
    client, _database = api_client
    response = client.post("/api/integrity/hash", files={"file": ("empty.bin", b"")})
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["sha256"] == EMPTY_SHA256
    assert body["result"]["verdict"] == "NOT VERIFIED"
    assert body["result"]["file_name"] == "empty.bin"
    assert body["status"] == "not_verified"


def test_matching_and_mismatching_digests(api_client):
    client, _database = api_client
    payload = b"project-file"
    digest = hashlib.sha256(payload).hexdigest()
    match = client.post(
        "/api/integrity/verify",
        files={"file": ("notes.txt", payload)},
        data={"reference_digest": digest.upper()},
    )
    assert match.status_code == 200
    assert match.json()["result"]["verdict"] == "MATCH"
    other = hashlib.sha256(b"different").hexdigest()
    mismatch = client.post(
        "/api/integrity/verify",
        files={"file": ("notes.txt", payload)},
        data={"reference_digest": other},
    )
    assert mismatch.json()["result"]["verdict"] == "MISMATCH"
    assert mismatch.json()["status"] == "failed"


def test_invalid_reference_digest(api_client):
    client, _database = api_client
    response = client.post(
        "/api/integrity/verify",
        files={"file": ("notes.txt", b"abc")},
        data={"reference_digest": "not-a-digest"},
    )
    assert response.status_code == 400


def test_oversized_file(small_client):
    client, _database = small_client
    response = client.post("/api/integrity/hash", files={"file": ("big.bin", b"12345")})
    assert response.status_code == 413


def test_binary_file_hash_matches_hashlib(api_client):
    client, _database = api_client
    payload = bytes(range(256)) + b"\x00\xff\xfe"
    digest = hashlib.sha256(payload).hexdigest()
    hashed = client.post("/api/integrity/hash", files={"file": ("blob.bin", payload)})
    assert hashed.status_code == 200
    assert hashed.json()["result"]["sha256"] == digest
    assert hashed.json()["result"]["verdict"] == "NOT VERIFIED"
    compared = client.post(
        "/api/integrity/verify",
        files={"file": ("blob.bin", payload)},
        data={"reference_digest": digest},
    )
    assert compared.json()["result"]["verdict"] == "MATCH"


def test_filename_does_not_keep_directories(api_client):
    client, _database = api_client
    response = client.post("/api/integrity/hash", files={"file": ("../../secret.txt", b"abc")})
    assert response.status_code == 200
    assert response.json()["result"]["file_name"] == "secret.txt"
    assert ".." not in response.json()["result"]["file_name"]


def test_hmac_empty_inputs_are_rejected(api_client):
    client, _database = api_client
    blank_message = client.post("/api/hmac/generate", json={"message": "", "secret": "secret"})
    assert blank_message.status_code == 422
    blank_secret = client.post("/api/hmac/verify", json={"message": "hello", "secret": "", "tag": "ab" * 32})
    assert blank_secret.status_code == 422
    bad_tag = client.post("/api/hmac/verify", json={"message": "hello", "secret": "secret", "tag": "zz" * 32})
    assert bad_tag.status_code == 400


def test_hmac_round_trip_and_tampering():
    secret = "correct-horse"
    tag = compute_tag("hello", secret)
    assert verify_tag("hello", secret, tag)
    assert not verify_tag("hello!", secret, tag)
    assert not verify_tag("hello", "wrong-horse", tag)
    assert not verify_tag("hello", secret, "ab" * 32)


def test_hmac_api_does_not_store_secret_or_tag(api_client):
    client, database = api_client
    secret = "hmac-secret-DO-NOT-PERSIST-7f3c9a"
    generated = client.post("/api/hmac/generate", json={"message": "classroom", "secret": secret})
    assert generated.status_code == 200
    tag = generated.json()["result"]["tag"]
    verified = client.post("/api/hmac/verify", json={"message": "classroom", "secret": secret, "tag": tag})
    assert verified.json()["result"]["verdict"] == "VALID"
    tampered = client.post("/api/hmac/verify", json={"message": "classroom!", "secret": secret, "tag": tag})
    assert tampered.json()["result"]["verdict"] == "INVALID"
    wrong_tag = client.post(
        "/api/hmac/verify",
        json={"message": "classroom", "secret": secret, "tag": "cd" * 32},
    )
    assert wrong_tag.json()["result"]["verdict"] == "INVALID"
    raw = database.read_bytes()
    assert secret.encode() not in raw
    assert tag.encode() not in raw
    assert b"classroom" not in raw


def test_signature_round_trip_wrong_key_and_malformed(api_client):
    client, database = api_client
    private_one, public_one = generate_keypair()
    _private_two, public_two = generate_keypair()
    message = "sign-this-record"
    signature = sign_bytes(private_one, message.encode("utf-8"))
    assert verify_bytes(public_one, message.encode("utf-8"), signature)
    assert not verify_bytes(public_two, message.encode("utf-8"), signature)

    signed = client.post("/api/signatures/sign", json={"message": message, "private_key_pem": private_one})
    assert signed.status_code == 200
    body = signed.json()["result"]
    checked = client.post(
        "/api/signatures/verify",
        json={"message": message, "public_key_pem": body["public_key_pem"], "signature": body["signature"]},
    )
    assert checked.json()["result"]["verdict"] == "VALID"
    changed = client.post(
        "/api/signatures/verify",
        json={"message": message + "!", "public_key_pem": body["public_key_pem"], "signature": body["signature"]},
    )
    assert changed.json()["result"]["verdict"] == "INVALID"
    wrong = client.post(
        "/api/signatures/verify",
        json={"message": message, "public_key_pem": public_two, "signature": body["signature"]},
    )
    assert wrong.json()["result"]["verdict"] == "INVALID"
    malformed_key = client.post(
        "/api/signatures/verify",
        json={"message": message, "public_key_pem": "not-a-key", "signature": body["signature"]},
    )
    assert malformed_key.status_code == 400
    malformed_signature = client.post(
        "/api/signatures/verify",
        json={"message": message, "public_key_pem": public_one, "signature": "!!!!"},
    )
    assert malformed_signature.status_code == 400
    raw = database.read_bytes()
    assert b"BEGIN PRIVATE KEY" not in raw
    assert private_one.encode() not in raw


def test_rsa_keys_below_2048_bits_are_rejected(api_client):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    client, _database = api_client
    small = rsa.generate_private_key(public_exponent=65537, key_size=1024)
    private_pem = small.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = small.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    signed = client.post("/api/signatures/sign", json={"message": "too-small", "private_key_pem": private_pem})
    assert signed.status_code == 400
    assert "2048" in signed.json()["detail"]
    checked = client.post(
        "/api/signatures/verify",
        json={"message": "too-small", "public_key_pem": public_pem, "signature": "aaaa"},
    )
    assert checked.status_code == 400
    assert "2048" in checked.json()["detail"]
