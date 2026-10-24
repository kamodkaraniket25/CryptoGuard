"""Digest helpers. Comparisons of digests and tags use hmac.compare_digest."""

import hashlib
import hmac
import re

_SHA256_RE = re.compile(r"[0-9a-f]{64}")


def normalize_sha256(value: str) -> str:
    candidate = value.strip().lower()
    if candidate.startswith("sha256:"):
        candidate = candidate[7:]
    if not _SHA256_RE.fullmatch(candidate):
        raise ValueError("SHA-256 digest must be 64 hexadecimal characters.")
    return candidate


def digests_match(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def public_key_fingerprint(pem: str) -> str:
    return hashlib.sha256(pem.strip().encode("utf-8")).hexdigest()
