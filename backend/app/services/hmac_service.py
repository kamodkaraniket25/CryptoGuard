"""HMAC-SHA256 authentication. Secrets and tags are not persisted."""

import hashlib
import hmac
import secrets

from app.utils.security import digests_match


def generate_secret() -> str:
    return secrets.token_hex(32)


def compute_tag(message: str, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_tag(message: str, secret: str, tag: str) -> bool:
    expected = compute_tag(message, secret)
    return digests_match(expected, tag)
