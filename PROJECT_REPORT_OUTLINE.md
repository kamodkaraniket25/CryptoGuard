# CryptoGuard — Project report outline

Use this as the skeleton of the written report. The paragraphs are suggested content taken from the repository. Replace the bracketed student details on the title page. Do not add timing scores, accuracy percentages, or vulnerability counts unless you measure them and keep the method with the number.

The application title to print is:

**CryptoGuard — Cryptographic Integrity and Software Supply Chain Verification Platform**

Version in code: **1.0.0**.

---

## Title page

Suggested lines:

- CryptoGuard — Cryptographic Integrity and Software Supply Chain Verification Platform
- A local web application for SHA-256 integrity, HMAC-SHA256 authentication, and RSA-PSS digital signatures
- Student name: [your name]
- Enrolment number: [your number]
- Programme and department: [your programme]
- Guide: [guide’s name]
- Academic year: [year]

Do not invent a company or a funding body.

---

## Abstract

Suggested content, about 150 words:

Software is often accepted because a filename or a package name looks familiar. This project builds CryptoGuard, a local full-stack application that separates three checks. The FastAPI backend hashes an uploaded file with SHA-256 and compares it with a reference digest when one is supplied. It creates and checks HMAC-SHA256 tags without writing the shared secret to the database. It generates a 2048-bit RSA key pair and signs or verifies UTF-8 messages with RSA-PSS and SHA-256. The React interface shows PASS, FAIL, or NOT VERIFIED and explains the limit of each result. SQLite stores sanitized history. Additional modules parse `package.json` and `requirements.txt`, query the OSV service, optionally query NVD, and emit a CycloneDX 1.7 SBOM. A passed check is limited to the evidence submitted. The system does not detect malware and does not establish a real-world identity by itself.

---

## 1. Introduction

Explain, in this order:

- Software moves through a supply chain: publisher, download or dependency, and user.
- A changed file can keep the same name.
- A hash, a message authentication code, and a digital signature are different tools.
- CryptoGuard is a teaching platform that runs those tools and labels their limits.
- The demonstration path is dashboard, hash, HMAC, signature, and reports.

Mention the in-application full title and version. Say the work is an academic MVP running on one machine.

---

## 2. Problem statement

Use the four situations from the explanation note:

- A distributed file is modified.
- A download is compared with a published digest.
- A release message is edited after an HMAC tag was created.
- A signed record is checked with a public key.

Then state the non-goals in the same section, because examiners look for them:

- No malware verdict.
- No automatic trust in a reference, a secret, or a public key.
- No claim that an empty OSV response means the package is safe.
- No full SLSA or Sigstore implementation.

---

## 3. Objectives

**Implemented objectives**

- Compute SHA-256 of an uploaded file without executing it.
- Compare that digest with a user-supplied reference and return MATCH or MISMATCH.
- Return NOT VERIFIED when no reference is supplied.
- Generate and verify HMAC-SHA256, including a server-generated secret when the client omits one.
- Generate an RSA-2048 key pair, sign UTF-8 text, and verify RSA-PSS signatures.
- Present PASS, FAIL, and NOT VERIFIED in the interface.
- Persist sanitized history and export CSV and JSON.
- Keep secrets and private keys out of that history.

**Also implemented, as supporting modules**

- Provenance sign and verify for a small canonical JSON record.
- Manifest parsing, OSV queries, optional NVD lookup, and CycloneDX 1.7 SBOM generation.
- Health and source-availability endpoints.

**Not objectives of this version**

- User accounts, malware scanning, package installation, and a public deployment.

---

## 4. Existing system and proposed system

**Existing situation, described without naming a fake product.**  
A person compares files by name, or pastes a hash into a generic checksum tool, or reads “signed” without knowing which key was used. Those habits do not record the difference between “digest calculated” and “digest matched,” and they do not warn that a valid signature still needs a trusted public key.

**Proposed system.**  
CryptoGuard gives each check its own page, a backend implementation of the algorithm, a written limitation, and a history row. The proposed system is this repository, not a diagram of a system that was not built.

You can add a small comparison table:

| Question | Typical manual habit | CryptoGuard behaviour |
| --- | --- | --- |
| Was the file hashed? | A local checksum tool, often with no record | SHA-256 on the server, row stored |
| Was it compared? | Easy to forget | No reference produces NOT VERIFIED |
| Was a message authenticated? | Often confused with a hash | HMAC-SHA256 with a secret that is not stored |
| Was a record signed? | “Signed” with no algorithm named | RSA-2048 PSS-SHA256, private key not stored |

---

## 5. Requirements

**Functional**

- Upload a file up to 10 MB and obtain SHA-256.
- Accept an optional reference digest of 64 hex characters, with an optional `sha256:` prefix.
- Generate and verify HMAC-SHA256 over UTF-8 text.
- Generate RSA keys and sign or verify UTF-8 text.
- Show a distinct result for match, mismatch, and hash-only.
- List, filter, export, and delete history.
- Parse npm and requirements manifests, query OSV, and generate a schema-checked SBOM.

**Non-functional**

- Cryptography runs on the backend.
- Secrets are not written to `verification_records`.
- Files are read in chunks and not executed.
- API errors stay visible. The frontend does not replace a failed call with a successful placeholder.
- The interface states the limit of a passed check.

**Environment**

- Python 3.11 or newer, Node.js and npm, a browser.
- Network access only when OSV, NVD, or a remote schema status check is used.
- No API key for hashing, HMAC, signatures, provenance, SBOM generation, or OSV.

---

## 6. Technology stack

Write one short paragraph per item, using the “what, why, where” notes in `PROJECT_EXPLANATION.md`.

Include: Python, FastAPI, Uvicorn, Pydantic, React, TypeScript, Vite, Tailwind CSS, Axios, hashlib, hmac, secrets, the `cryptography` package, SQLAlchemy, SQLite, HTTPX, jsonschema, python-multipart, pytest, and Vitest.

Do not add a database, framework, or scanner that is not in `backend/requirements.txt` or `frontend/package.json`.

---

## 7. System architecture

Use the Mermaid diagram in `PROJECT_EXPLANATION.md`. Then explain four boundaries:

- Browser: forms, labels, downloads of returned JSON.
- API: validation and routing in `backend/app/api/routes.py`.
- Services: `integrity.py`, `hmac_service.py`, `signatures.py`, plus supply-chain services.
- SQLite: three tables in `backend/app/models/tables.py`.

Trace Compare Hashes from `IntegrityPage` through `verifyFile` to `/api/integrity/verify`, `read_upload_hashed`, `hash_result`, and `save_operation`. That trace is the architecture evidence. A screenshot of the PASS and FAIL badges can be added after you perform the demo. Do not draw a screenshot you did not take.

---

## 8. Methodology

Describe the build in the order the checks were made honest:

1. Define the result vocabulary: match, mismatch, not verified, valid, invalid.
2. Implement SHA-256 streaming and constant-time comparison.
3. Implement HMAC without persisting the secret.
4. Implement RSA-PSS with an explicit key size and padding.
5. Store sanitized history.
6. Add the React pages and map backend verdicts to PASS, FAIL, and NOT VERIFIED.
7. Add provenance, OSV, and SBOM as separate modules with their own limitation text.
8. Test the cryptography and the “empty OSV is not safety” case.

This is a construction method, not a user study. Do not invent survey results.

---

## 9. Implementation

Suggested subsections, each pointing at a file:

- **File integrity.** `backend/app/utils/files.py`, `backend/app/services/integrity.py`, `frontend/src/pages/IntegrityPage.tsx`.
- **HMAC.** `backend/app/services/hmac_service.py`, routes `hmac_generate` and `hmac_verify`, `frontend/src/pages/HmacPage.tsx`.
- **Signatures.** `backend/app/services/signatures.py`, `frontend/src/pages/SignaturePage.tsx`. State the key size, exponent, PSS parameters, and base64 encoding.
- **History.** `verification_records`, `backend/app/services/history.py`, Reports page.
- **Supply chain.** Manifest parser, OSV client, NVD client behind `nvd_enabled`, SBOM generator, provenance canonical JSON.
- **Interface.** Dashboard, sidebar, and in-app documentation. Mention that charts use database counts.

Include the known empty-file digest only as the test vector in `test_crypto.py`, not as a measurement of your demo file.

---

## 10. Testing and results

Write this section from the tests that exist. Do not invent a pass rate.

**Backend, pytest**

- Empty file hashes to the standard SHA-256 test vector and is `NOT VERIFIED`.
- A matching reference, including a different letter case, is `MATCH`. A different digest is not.
- An invalid reference is rejected.
- An upload over the configured limit is rejected.
- Directory prefixes are removed from filenames.
- HMAC verification fails when the message is tampered with.
- The HMAC secret and tag are not stored on the history row.
- Signatures verify with the matching key, fail with the wrong material, and reject malformed input.
- History can be exported and deleted. Dashboard counts come from stored rows. Health checks the database.
- SBOM output validates against the CycloneDX 1.7 schema in the tree.
- An empty OSV body is not treated as proof of safety.
- Provenance can show a missing digest or signature, and a signed record can match an uploaded artifact.

**Frontend, Vitest**

- Navigation links point at the real routes.
- An empty dashboard state is shown when the stats API returns zero operations.
- Hash Checker requires a file, shows a loading state, then shows PASS for a MATCH response, and shows an API error when the request fails.
- Short digests and short HMAC tags are rejected in the form helpers.
- Source cards render the status returned by the API.

**What not to write**

- No throughput in megabytes per second unless you measure it and describe the machine.
- No “100% security” sentence.
- No sample malware result.

You may paste a real PASS and FAIL screenshot from your own demo in an appendix.

---

## 11. Security considerations

Cover:

- SHA-256 equality versus trust in the reference.
- `hmac.compare_digest` for digests and tags.
- HMAC secret generated with `secrets.token_hex` and omitted from history.
- RSA private key returned once, unencrypted PEM, not stored.
- Public-key fingerprint is not an identity.
- Upload size limit, chunked read, no execution, filename cleaning.
- Separate handling of HTTP 400, connection failure, and cryptographic FAIL.
- OSV and NVD failures are source failures. Cache expiry defaults to 6 hours.
- No authentication layer in front of the local API.

---

## 12. Limitations

Use the list in section 16 of `VIVA_QUESTIONS.md`. Keep the tone factual. The strongest limitations to give space to are:

- trusted reference required,
- shared-secret distribution,
- public-key identity trust,
- no malware detection,
- provenance is not SLSA,
- single-user local deployment.

---

## 13. Future scope

Only items that are not already built:

- Trusted public-key labelling.
- Encrypted or externally held private keys.
- Access control and a hardened deployment.
- A fuller build-attestation format, if a later course covers it.
- Broader automated end-to-end tests.

State that OSV lookup and CycloneDX export are present now, so they are not future fiction. NVD is present but disabled by default. Enabling it is configuration, not a new algorithm.

---

## 14. Conclusion

Close on the claim the software can actually support:

CryptoGuard demonstrates file integrity, message authentication, and digital signatures as three different checks. It records the checks, withholds secrets from that record, and states what a passed result does not prove. That is the useful cybersecurity lesson of the project.

---

## 15. References

Cite only documents you used. Suitable primary references, because the code calls these systems or standards:

- NIST FIPS 180-4, Secure Hash Standard, for SHA-256. https://csrc.nist.gov/publications/detail/fips/180/4/final
- NIST FIPS 198-1, The Keyed-Hash Message Authentication Code (HMAC). https://csrc.nist.gov/publications/detail/fips/198/1/final
- RFC 8017, PKCS #1: RSA Cryptography Specifications, which defines RSASSA-PSS. https://www.rfc-editor.org/rfc/rfc8017
- Python documentation for `hashlib`, `hmac`, and `secrets`. https://docs.python.org/3/library/hmac.html
- The `cryptography` library documentation for RSA-PSS. https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/
- FastAPI documentation. https://fastapi.tiangolo.com/
- OSV API documentation. https://google.github.io/osv.dev/api/
- NVD vulnerability API, only if you discuss the optional module. https://nvd.nist.gov/developers/vulnerabilities
- CycloneDX 1.7 JSON specification, because the SBOM module targets it. https://cyclonedx.org/docs/1.7/json/

Do not cite papers you did not read. Do not add a fake “experimental results” paper.

---

## Appendix ideas

- API list from `backend/app/api/routes.py`, grouped by integrity, HMAC, signatures, provenance, supply chain, sources, and history.
- One sample JSON response from a real `/api/integrity/verify` call, with the verdict visible.
- The demo steps from `HOD_DEMO_SCRIPT.md`.
- Screenshots you capture yourself of NOT VERIFIED, PASS, and FAIL.
