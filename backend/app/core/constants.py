"""Operation names, statuses, and user-facing limitation statements."""

PRODUCT_NAME = "CryptoGuard"
FULL_TITLE = (
    "CryptoGuard — Cryptographic Integrity and Software Supply Chain Verification Platform"
)

NO_MATCH_MESSAGE = (
    "No matching advisory returned by this source for the queried package and version."
)


class Op:
    HASH = "hash"
    HASH_VERIFY = "hash_verify"
    HMAC_GENERATE = "hmac_generate"
    HMAC_VERIFY = "hmac_verify"
    SIGNATURE_KEYGEN = "signature_keygen"
    SIGNATURE_SIGN = "signature_sign"
    SIGNATURE_VERIFY = "signature_verify"
    PROVENANCE_VERIFY = "provenance_verify"
    PROVENANCE_SIGN = "provenance_sign"
    DEPENDENCY_SCAN = "dependency_scan"
    VULNERABILITY_QUERY = "vulnerability_query"
    SBOM_GENERATE = "sbom_generate"


class Status:
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"
    NOT_VERIFIED = "not_verified"


LIMITATIONS: dict[str, list[str]] = {
    Op.HASH: [
        "A SHA-256 digest identifies the exact bytes that were hashed.",
        "Without a trusted reference digest, CryptoGuard cannot decide MATCH or MISMATCH.",
        "A digest does not prove who published the file or that the software is safe to run.",
    ],
    Op.HASH_VERIFY: [
        "A matching SHA-256 digest shows the file bytes are equal to the supplied reference.",
        "A match does not prove publisher identity, a secure build, or overall software safety.",
        "The reference digest is only as trustworthy as the place you copied it from.",
    ],
    Op.HMAC_GENERATE: [
        "HMAC-SHA256 shows that someone who knows the shared secret produced this tag.",
        "Both parties must already possess the same secret. CryptoGuard does not distribute it.",
        "The secret and tag are returned once and are not written to the database.",
    ],
    Op.HMAC_VERIFY: [
        "A valid tag means this message and this shared secret produce the presented tag.",
        "An invalid tag means the message, secret, or tag does not match. CryptoGuard does not say which one changed.",
        "The secret was not stored and was not sent to any vulnerability data source.",
    ],
    Op.SIGNATURE_KEYGEN: [
        "The private key is shown once so you can copy it. CryptoGuard does not store it.",
        "Protect the private key. Anyone who has it can create signatures that verify with this public key.",
        "A public key does not by itself prove a real-world identity.",
    ],
    Op.SIGNATURE_SIGN: [
        "The signature covers the exact UTF-8 bytes of the message you submitted.",
        "The private key was used only to create this signature and was not stored.",
        "A valid signature later proves key possession, not a trusted identity, unless you already know who owns the public key.",
    ],
    Op.SIGNATURE_VERIFY: [
        "VALID means this public key accepts the signature over these exact UTF-8 bytes.",
        "INVALID means the bytes, signature, or public key do not agree.",
        "A valid signature proves a trusted identity only when public-key ownership is established independently.",
    ],
    Op.PROVENANCE_VERIFY: [
        "Digest status and signature status are separate. One does not imply the other.",
        "Unsigned JSON is not authenticated evidence.",
        "A structurally valid record is not SLSA compliance and is not proof of a secure build.",
        "A digest match shows byte equality with the uploaded artifact. It does not prove the build environment was safe.",
    ],
    Op.PROVENANCE_SIGN: [
        "The signature covers a canonical UTF-8 JSON document, not the raw text you pasted.",
        "The signed keys are artifact_sha256, builder_id, build_timestamp, source_repository, and source_revision.",
        "The private key was not stored. A valid signature does not prove identity unless the public key is already trusted.",
    ],
    Op.DEPENDENCY_SCAN: [
        "Manifests are parsed only. Packages are not installed, and scripts are not executed.",
        NO_MATCH_MESSAGE + " That is not the same as saying no vulnerabilities exist.",
        "Version ranges are policy warnings. They are not sent to OSV as if they were exact versions.",
        "A package name alone is not evidence that a package is malicious.",
    ],
    Op.VULNERABILITY_QUERY: [
        NO_MATCH_MESSAGE + " That is not the same as saying no vulnerabilities exist.",
        "An unavailable data source is not evidence of safety.",
        "Cached results show the time they were retrieved. They are not a promise of later freshness.",
    ],
    Op.SBOM_GENERATE: [
        "This SBOM lists components declared by the uploaded manifest. It can be incomplete.",
        "Unknown suppliers, licenses, hashes, and transitive dependencies are omitted rather than guessed.",
        "Generating an SBOM is not the same as detecting vulnerabilities.",
    ],
}


CANONICALIZATION_RULE = (
    "Provenance signatures cover the UTF-8 encoding of a JSON object with sorted keys and no extra whitespace. "
    "The object contains exactly these string fields: artifact_sha256, builder_id, build_timestamp, "
    "source_repository, and source_revision. artifact_sha256 is 64 lowercase hexadecimal characters with no prefix. "
    "The signature, public key, artifact file, and any extra JSON fields are not part of the signed bytes. "
    "The algorithm is RSA-2048, RSA-PSS, MGF1-SHA256, salt length equal to the SHA-256 digest length, and SHA-256."
)
