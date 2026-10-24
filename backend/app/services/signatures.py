"""RSA-PSS signatures. Private keys are not persisted or logged."""

import base64

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

ALGORITHM = "RSA-2048-PSS-SHA256"
MIN_RSA_BITS = 2048


def _padding() -> padding.PSS:
    return padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.DIGEST_LENGTH,
    )


def generate_keypair() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


def _require_rsa_size(key: RSAPrivateKey | RSAPublicKey) -> None:
    if key.key_size < MIN_RSA_BITS:
        raise ValueError(f"RSA keys must be at least {MIN_RSA_BITS} bits.")


def _load_private(pem: str) -> RSAPrivateKey:
    try:
        key = serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    except (ValueError, TypeError) as exc:
        raise ValueError("Private key is not a valid unencrypted PEM encoding.") from exc
    if not isinstance(key, RSAPrivateKey):
        raise ValueError("Only RSA private keys are supported.")
    _require_rsa_size(key)
    return key


def _load_public(pem: str) -> RSAPublicKey:
    try:
        key = serialization.load_pem_public_key(pem.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise ValueError("Public key is not a valid PEM encoding.") from exc
    if not isinstance(key, RSAPublicKey):
        raise ValueError("Only RSA public keys are supported.")
    _require_rsa_size(key)
    return key


def _decode_signature(signature_b64: str) -> bytes:
    try:
        return base64.b64decode(signature_b64.strip(), validate=True)
    except Exception as exc:
        raise ValueError("Signature is not valid base64.") from exc


def public_pem_from_private(private_pem: str) -> str:
    key = _load_private(private_pem)
    return key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


def sign_bytes(private_pem: str, payload: bytes) -> str:
    key = _load_private(private_pem)
    signature = key.sign(payload, _padding(), hashes.SHA256())
    return base64.b64encode(signature).decode("ascii")


def verify_bytes(public_pem: str, payload: bytes, signature_b64: str) -> bool:
    signature = _decode_signature(signature_b64)
    key = _load_public(public_pem)
    try:
        key.verify(signature, payload, _padding(), hashes.SHA256())
        return True
    except InvalidSignature:
        return False
