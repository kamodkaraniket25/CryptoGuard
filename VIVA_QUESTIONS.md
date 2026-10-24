# CryptoGuard — Viva questions and answers

Answer in your own words. These replies match the code in this repository. They do not claim that a PASS result makes software safe.

The on-screen words are PASS, FAIL, and NOT VERIFIED. The API words are `MATCH`, `MISMATCH`, `NOT VERIFIED`, `VALID`, and `INVALID`. The frontend maps MATCH and VALID to PASS, and MISMATCH and INVALID to FAIL.

---

## Required questions

### 1. Why did you choose this project?

Software is often trusted because the filename looks right. I wanted a project that shows the difference between a hash, a shared-secret tag, and a digital signature, using real algorithms rather than a diagram only. CryptoGuard makes that difference visible, and it also shows the limit of each result.

### 2. What is the main problem statement?

A file, a message, or a release record can be changed during distribution and still look ordinary. People then confuse “I have a fingerprint” with “I trust the publisher” or “this program is safe.” CryptoGuard checks the evidence you supply and refuses to upgrade that result into a broader safety claim.

### 3. Why are three different cryptographic techniques needed?

They answer three different questions. SHA-256 asks whether file bytes match a reference digest. HMAC-SHA256 asks whether a shared secret authenticates a message. RSA-PSS asks whether a private key signed a record that a public key can check. One technique does not replace the others. A hash has no key. HMAC uses one shared secret, so either party can create tags. A signature uses a private key that verifiers do not need.

### 4. Why is SHA-256 not encryption?

Encryption is reversible with a key. SHA-256 is a one-way digest. CryptoGuard never decrypts a hash, because there is nothing to decrypt. The code in `backend/app/utils/files.py` only calls `hashlib.sha256()` and returns 64 hex characters. The application does not encrypt uploaded files.

### 5. Can two files ever have the same hash?

In theory, yes. That is a collision. SHA-256 produces 256-bit digests, and no collision is practical to construct for this project. CryptoGuard does not claim SHA-256 is mathematically incapable of a collision. It treats equal digests as strong evidence that the bytes are equal, which is the standard engineering interpretation. The code does not try to prove the absence of all collisions.

### 6. What happens if a file changes by one byte?

The SHA-256 digest changes in a way that looks unrelated to the original digest. That behaviour is called the avalanche effect. In the demo, you do not need to edit the file. Changing one hex character of the reference produces FAIL, because the calculated digest and the reference no longer match. If the file itself changes, the calculated digest changes and a comparison with the old reference also fails.

### 7. What is HMAC?

HMAC means Hash-based Message Authentication Code. CryptoGuard implements HMAC-SHA256. The message and a shared secret are the inputs. `hmac.new` in `backend/app/services/hmac_service.py` uses SHA-256 and returns a 64-character hex tag. A valid tag shows that someone who knows the secret produced it for those exact UTF-8 bytes.

### 8. Why does HMAC require a secret key?

Without a secret, anyone who can edit the message can also recompute the tag. The secret is what makes the tag hard to forge. Both sides must already know it. If the user omits the secret, the API generates 32 random bytes with `secrets.token_hex(32)`. CryptoGuard does not send that secret to another user for you.

### 9. What happens if someone steals the HMAC secret?

They can create new tags that verify for any message, and they can check tags you create. HMAC then stops distinguishing the attacker from the legitimate partner. The secret must be replaced. A valid tag after theft does not identify which person used the secret. The application cannot detect that the secret was stolen.

### 10. Why do digital signatures use two keys?

The private key creates the signature. The public key checks it. Verifiers do not need the private key, so the signer does not have to share the ability to sign. That is different from HMAC, where the same secret both creates and checks tags. In this project the pair is a 2048-bit RSA key with public exponent 65537.

### 11. Why should a private key never be shared?

Anyone who has the private key can create signatures that this public key will accept. Receivers would not be able to tell those signatures apart from the owner’s. CryptoGuard returns the private key once and does not write it into SQLite. The PEM is unencrypted PKCS#8, so a copy in a chat or a screenshot is still a real key. Hiding it in the browser is not the same as protecting a stored key.

### 12. What is RSA-PSS?

PSS means Probabilistic Signature Scheme. It is a signature padding method for RSA. CryptoGuard uses RSA-PSS with MGF1-SHA256, a salt length equal to the SHA-256 digest length, and SHA-256 as the message hash. The code is `_padding()` and `key.sign` in `backend/app/services/signatures.py`. The signature is then base64-encoded. PSS includes randomness, so two signatures of the same message with the same key are not expected to look identical. Verification still succeeds for each valid one.

### 13. What does PASS mean in your application?

PASS means the evidence for that specific check matched. For a file, the backend verdict was `MATCH`: the SHA-256 digest equals the reference you entered. For HMAC or a signature, the backend verdict was `VALID`. The page text says what matched. PASS does not mean “safe,” “authentic person,” or “no vulnerabilities.”

### 14. Does a PASS result mean the software is completely safe?

No. The limitation text returned by the API says a matching digest does not prove publisher identity, a secure build, or overall software safety. A valid HMAC does not identify a person. A valid signature proves key use, not a trusted identity, unless you already trust the public key. There is no malware scanner.

### 15. Can your project identify malware?

No. Nothing in the backend inspects a file for malware, and packages are not installed or executed. A dependency scan only parses a manifest and asks OSV about exact versions. An empty OSV response is described as no matching advisory, not as proof that no vulnerability exists.

### 16. What are the current limitations?

The reference digest is only as good as its source. The HMAC secret must be shared outside the app and must stay secret. The public key is trusted only if you decide to trust it. Private keys are not stored on the server, but they are unencrypted in the browser session. Uploads are limited to 10 MB and are not executed, which is not a sandbox. There are no user accounts. Provenance is a small signed JSON record, not SLSA or Sigstore. NVD lookup exists but is disabled unless configured. The tests are functional tests, not a penetration test.

### 17. How did you test your implementation?

The backend uses pytest. `backend/tests/test_crypto.py` checks SHA-256 against `hashlib`, the known empty-file digest, a matching digest, a mismatch, a bad reference, an oversized upload, HMAC tampering, the absence of the secret in stored history, and signature success, failure, and malformed input. `test_history.py` checks export, delete, dashboard counts, and health. `test_supply.py` checks manifest parsing, the CycloneDX schema, OSV behaviour including an empty result, and provenance. The frontend uses Vitest and Testing Library for navigation, the empty dashboard, hash-page errors, and form validation. I would not describe these as performance benchmarks. I have not put timing numbers in the report because the tests do not produce a benchmark score.

### 18. What improvements would you add in the future?

I would add a way to label trusted public keys, stronger protection for private keys, and access control if the app were ever hosted for more than one user. Provenance could grow toward a fuller build attestation. The dependency scanner and CycloneDX SBOM are already implemented, so I would extend them rather than pretend they are missing. I would also add more end-to-end tests. I would not add malware claims unless a real scanner was integrated and its limits were shown.

---

## Project overview and motivation

### 19. What is CryptoGuard in one sentence?

It is a local web application that checks file integrity, message authentication, and digital signatures, and records those checks without storing secrets.

### 20. Who is it for?

A student, a lab pair, or a teaching assistant running it on one machine. It is an academic MVP. It is not a multi-user production service.

### 21. What does the title on the screen say?

The product name is CryptoGuard. The full title in code is “Cryptographic Integrity and Software Supply Chain Verification Platform.” Version 1.0.0 is returned by `/api/health`.

---

## Software supply chain integrity

### 22. What is a software supply chain?

It is the path by which software reaches the person who runs it: a download, a dependency, a build output, or a release note. Integrity here means the bytes match a trusted description. It is not a promise that the program has no bugs.

### 23. Why is a filename not evidence?

The name is chosen by whoever sends the file. CryptoGuard hashes bytes. `safe_filename` also strips any directory path so the stored name is only a base name. The name is not an input to SHA-256.

---

## SHA-256, collisions, and the avalanche effect

### 24. How does CryptoGuard calculate the file hash?

`read_upload_hashed` reads the upload in 64 KiB chunks, updates a SHA-256 hasher, stops above 10 MiB, closes the file, and returns the hex digest. The file bytes are not written to SQLite.

### 25. What is NOT VERIFIED?

It is the result of `POST /api/integrity/hash`, or any hash saved with status `not_verified`. The digest exists, but no reference was compared. The UI must not call that a PASS. The empty-file test expects both the standard empty digest and the verdict `NOT VERIFIED`.

### 26. Why must the reference come from a trusted source?

The algorithm only tests equality. If an attacker supplies both the file and the digest, equality is expected and still tells you nothing about the real publisher. The limitation list for `hash_verify` says the reference is only as trustworthy as the place you copied it from.

### 27. Does the comparison stop at the first different character?

No. `digests_match` uses `hmac.compare_digest`. That is a constant-time comparison for the two strings. It is used for SHA-256 references and for HMAC tags.

---

## HMAC and shared secrets

### 28. What is a shared secret in your project?

It is a UTF-8 string known to the sender and the verifier. It is not stored in `verification_records`. The generate response shows it once so the demo can continue. The history metadata stores the message length and whether the server generated the secret, not the secret itself.

### 29. What if the tag is the wrong length?

`/api/hmac/verify` returns HTTP 400: the tag must be 64 hexadecimal characters. The page shows that as an input error. It does not show FAIL, because verification did not run.

### 30. Why is HMAC not a digital signature?

The same secret creates and checks the tag, so either holder can produce a valid tag. You cannot later prove which of them did it. That is why HMAC does not provide non-repudiation. A signature is different because verifiers do not hold the private key.

---

## Digital signatures, RSA, and keys

### 31. What algorithm and key size do you actually use?

RSA-2048, RSA-PSS, MGF1-SHA256, salt length equal to the SHA-256 digest, and SHA-256 over the message bytes. The algorithm string stored on the operation is `RSA-2048-PSS-SHA256`.

### 32. What is the difference between signature validity and identity trust?

Validity means this public key accepts this signature over these bytes. Identity trust means you have a separate reason to believe the key belongs to a particular person. CryptoGuard answers validity. The verify limitation text says a valid signature proves a trusted identity only when public-key ownership is established independently.

### 33. What happens if the message gains one character?

The signed bytes change. `verify_bytes` raises `InvalidSignature`, the API returns `INVALID`, and the page shows FAIL. A malformed key or a signature that is not base64 is HTTP 400, not FAIL.

### 34. Do you store the public key?

The private key is not stored. For sign and verify, metadata can include `public_key_sha256`, which is SHA-256 of the PEM text from `public_key_fingerprint`. That fingerprint is not an X.509 certificate and not a person’s identity.

---

## Authentication, authorization, encryption, and hashing

### 35. What is the difference between authentication and integrity?

Integrity asks whether the bytes are unchanged relative to a reference. Authentication asks whether a secret or a key approves those bytes. SHA-256 comparison is an integrity check against a digest you supply. HMAC and RSA-PSS are authentication checks, and they also detect changes, because a changed message no longer matches the tag or signature.

### 36. What is the difference between authentication and authorization?

Authentication is evidence about who approved a message, or in HMAC’s case, evidence that the shared secret was used. Authorization is whether that identity is allowed to do something. CryptoGuard has no login and no permissions. It does not authorize users. A valid signature is not an access-control decision.

### 37. Why does a hash alone not authenticate a sender?

Anyone can hash a file. There is no secret and no private key in `hashlib.sha256()`. The digest identifies bytes. It does not identify a person. That is why a hash with no trusted reference is NOT VERIFIED, and why even a match does not name the publisher.

---

## Architecture, data, and errors

### 38. What are the main parts of the system?

A React frontend, a FastAPI backend, cryptographic service functions, and SQLite through SQLAlchemy. OSV is called for dependency and vulnerability queries. NVD is optional and off by default. The CycloneDX schema file is local.

### 39. Where does cryptography run?

On the server. The browser collects the file, message, secret, or key and displays the JSON result. The SHA-256 of the public PEM shown on the signature page is only a local fingerprint of text already on the form. Signing and verifying still call `/api/signatures/sign` and `/api/signatures/verify`.

### 40. What is stored in the database?

`verification_records` stores the operation id, type, status, algorithm, filename, size, digest when the operation is a file hash, time, duration, and sanitized metadata. `vulnerability_lookup_cache` stores OSV or NVD responses until they expire. `data_source_checks` stores source availability checks. File bytes, HMAC secrets, and private keys are not columns.

### 41. How are errors separated from FAIL?

FAIL is a completed cryptographic comparison that did not match. HTTP 400 is bad input. A missing backend is a connection error from Axios. HTTP 503 on health means the database check failed. An OSV timeout is a source failure. The interface is written so those are not displayed as a hash mismatch.

---

## Supply-chain modules and testing

### 42. Is OSV the same as your hash checker?

No. OSV is an external advisory service. The dependency scanner parses a manifest and queries exact package versions. A hash checker never calls OSV. An OSV outage does not make `/api/health` fail. Health only checks the app and SQLite.

### 43. What does the SBOM prove?

`POST /api/sbom/generate` builds a CycloneDX 1.7 JSON document from declared components and validates it with jsonschema against the schema in the repository. Unknown licenses and transitive dependencies are omitted. The limitation text says generating an SBOM is not the same as detecting vulnerabilities.

### 44. What is the provenance feature, and what is it not?

You can sign five canonical fields of a small JSON record with the same RSA-PSS algorithm, and you can verify the signature and, if you upload an artifact, the digest separately. Unsigned JSON is not treated as authenticated evidence. The code says a structurally valid record is not SLSA compliance.

### 45. What would you not claim in the viva?

I would not claim malware detection, user authentication, encrypted private-key storage, a trusted certificate authority, SLSA compliance, or that PASS means the software is safe. I would not quote a digest for the demo file unless I had just calculated it on screen.
