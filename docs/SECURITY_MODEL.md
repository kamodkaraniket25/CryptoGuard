# Security model

CryptoGuard is an academic integrity and supply-chain demonstration. It is not a production certification system, a malware scanner, or a substitute for a vendor's signed release process.

## Assets

- Uploaded file bytes, while they are being hashed
- Manifest text, while it is being parsed
- HMAC shared secrets
- RSA private keys
- Public keys and signatures
- Provenance records
- Local verification history
- Cached vulnerability responses
- Optional NVD API key in the backend environment

## Trust boundaries

| Boundary | What crosses it |
| --- | --- |
| Browser to local backend | Files, messages, manifests, public keys, and, when the user asks to sign, private keys and HMAC secrets |
| Backend to OSV | Package name, ecosystem, and exact version only |
| Backend to NVD | A CVE identifier, and the API key header when configured |
| Backend to CycloneDX schema host | A GET of the published schema URL during an explicit status check |
| Backend to SQLite | Sanitized operation summaries, cache payloads, and source-check rows |

## Threats and mitigations

- **Tampered file.** SHA-256 is compared with `hmac.compare_digest` against a user-supplied reference. A match only proves byte equality with that reference.
- **Forged HMAC tag.** Tags are HMAC-SHA256. Verification uses `hmac.compare_digest`. The database and logs are not given the secret or the tag.
- **Stolen private key.** Keys are generated in memory, returned to the user, and not stored. The user is warned to protect them. The intended host is localhost.
- **Malformed keys or signatures.** PEM and base64 parsing errors become a 400 response or a `NOT_VERIFIED` provenance note. They do not return a stack trace.
- **Malicious upload.** Files are read in chunks, size-limited, and never executed, extracted, or installed. Filenames keep only the base name.
- **Path traversal.** Stored names pass through `Path.name` and a printable-character filter.
- **Oversized body.** Uploads stop at `MAX_UPLOAD_BYTES`. JSON bodies over `JSON_BODY_LIMIT_BYTES` are rejected from the Content-Length header.
- **Secret leakage through validation errors.** Request validation responses omit the submitted input.
- **Confused source outage.** Timeouts and HTTP errors are stored as source failures. The UI does not treat them as "no vulnerabilities."
- **Cache staleness.** Cached rows expire. The retrieval time is shown. Refresh bypasses the cache.
- **Cross-origin browser calls.** CORS allows only the origins in `CORS_ORIGINS`.
- **Double-counting CVEs.** Dashboard findings use one canonical id, preferring a CVE alias when OSV provides one.

## Residual risks

- A person who runs the backend on a shared server will send private keys and HMAC secrets to that server. The project is designed for a local machine.
- A matching hash or a valid signature does not establish a real-world identity by itself.
- OSV and NVD can be unavailable, delayed, or incomplete. Absence of a record is not safety.
- A manifest SBOM misses transitive dependencies, licenses, and file hashes that the manifest does not contain.
- This build does not authenticate users. Anyone who can reach the API can use it and read the local history.
- RSA 2048 and an unencrypted PKCS#8 PEM are appropriate for a classroom demo. They are not a full key-management design.

## Logging

The backend does not log request bodies. Unexpected exceptions are logged on the server and returned to the client as a generic message.
