# CryptoGuard — HOD demonstration script

Aim for about 6 minutes. Speak in short sentences. Use a file you create during the demo, and read the digest from the screen. Do not memorise a hash.

Before you walk in:

1. Start the backend from the `backend` folder: `npm run dev`, or `.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
2. Start the frontend from the `frontend` folder: `npm run dev`.
3. Open `http://127.0.0.1:5173`.
4. Confirm the sidebar says **Backend connected** and **API ok · database ok**. If it does not, fix that before the presentation. A dead API must be described as a connection failure, never as a PASS.
5. Create `release-note.txt` on the desktop in Notepad. Put one line in it: `Release candidate 1.4.0`. Save it. You will hash this real file.
6. Have this script beside you. You do not need sample PASS data. The buttons create real results.

If a click fails, read the red message. Say: “That is an input error” or “That is the backend being unavailable.” Do not call it a cryptographic failure unless the badge says FAIL.

---

## Opening

**Say this.**

“Good morning. This is CryptoGuard, a local platform for software supply chain integrity. The problem is that a file or a message can be changed and still look normal. I will show three checks. SHA-256 compares file bytes with a reference digest. HMAC-SHA256 checks a shared secret. RSA-PSS checks a signature with a public key. PASS only means the evidence I submitted matched. It does not mean the software is free of malware.”

**Time.** About 30 seconds.

---

## 1. Introduce the purpose

**Click.** Stay on the dashboard at `/`.

**Expect.** The heading, the tagline “Verify Integrity. Authenticate Messages. Trust Digital Signatures.”, three feature cards, and the workflow Input, Cryptographic verification, Result.

**Say.**

“The supply chain is the path from a publisher to the person who runs the software. CryptoGuard does not claim to secure that whole path. It answers a smaller question with a real algorithm, and it labels the limit of the answer.”

**Concept.** Problem scope. You are not claiming malware detection.

---

## 2. Explain the dashboard

**Click.** Point to SHA-256 Integrity, HMAC Authentication, and Digital Signatures. Then point to PASS, FAIL, and NOT VERIFIED. If history rows are visible, point to one real row and to System health.

**Expect.** Health shows the live `/api/health` result. Counts and the chart appear only when SQLite has operations. An empty database shows an empty state and a button to perform the first verification. Those counts are not typed in by hand.

**Say.**

“PASS means the evidence matched. FAIL means it did not. NOT VERIFIED means I calculated something but did not have the reference needed for a decision. The health line is the backend and the database. It is not a threat level.”

**Concept.** Honest result labels, and a dashboard driven by stored records.

---

## 3. Calculate a real SHA-256 digest

**Click.** Start Verification, or Hash Checker in the sidebar.

**Input.** Drag `release-note.txt` into the file area. Do not type a reference yet.

**Click.** Calculate SHA-256.

**Expect.** The badge says NOT VERIFIED. A 64-character hex digest appears. The filename and size match the file you chose. The technical result from the API is `NOT VERIFIED`.

**Say.**

“The backend streamed the file through SHA-256 and did not run it. This digest is a fingerprint of these exact bytes. I have not compared it with anything, so the result is NOT VERIFIED, not PASS. A fingerprint alone does not say who wrote the file.”

**Concept.** Hash calculation is not verification.

---

## 4. Show PASS

**Click.** Copy digest. Paste it into Reference digest. Click Compare Hashes.

**Expect.** The badge says PASS. The technical result is `MATCH`. The explanation says the bytes match the reference you supplied, and that this does not name the publisher.

**Say.**

“I am using the digest I just calculated as the reference, which is what I would do if the course page had published this value. PASS means the uploaded bytes match that reference. I still have to trust the place the reference came from. If I had copied the digest from an attacker, a match would only prove that the file matches the attacker’s digest.”

**Concept.** Integrity against a trusted reference. Trust in the reference is outside the hash.

---

## 5. Show FAIL

**Click.** In the reference box, change one hexadecimal character. If the first character is `a`, change it to `b`. It must remain 64 hex characters. Click Compare Hashes.

**Expect.** The badge says FAIL. The technical result is `MISMATCH`. The text says the calculated digest is different from the reference.

**Say.**

“One wrong character in the reference is enough. In real life this is what I would see if the file had been edited, or if I had the wrong published digest. FAIL means the bytes and the reference disagree. It does not, by itself, tell me who edited the file.”

If you type a short reference by mistake, the page will say the digest must be 64 hexadecimal characters. Say: “That is an input error. I will not call it FAIL, because the comparison did not run.”

**Concept.** A mismatch is a failed integrity check. Bad input is a different outcome.

---

## 6. Generate and verify an HMAC tag

**Click.** HMAC Verifier in the sidebar.

**Input.** Leave the message as “The backup completed at 02:00.” or type a short sentence of your own. Leave Shared secret empty.

**Click.** Generate authentication tag.

**Expect.** A warning that the secret is only in the browser. A secret and a 64-character tag appear. The verify panel is filled in. The secret is not a PASS result. Generation is recorded as a completed operation, not as a verification.

**Click.** Verify tag.

**Expect.** PASS. The technical result is `VALID`. The sentence says the tag matches this message and this secret, and that HMAC does not identify a person.

**Say.**

“HMAC stands for hash-based message authentication code. Both lab partners must already share this secret. The backend computed HMAC-SHA256 over the UTF-8 message. PASS means the tag, the message, and the secret agree. Anyone who knows the secret could have created it, so this is not a personal signature. The secret is not written into the history database. I can clear it from the page when I finish.”

**Concept.** Shared-secret authentication, and the absence of non-repudiation.

---

## 7. Show HMAC failure

**Click.** In the Verify panel only, change the message. For the default text, change `02:00` to `03:00`. Do not change the tag. Click Verify tag.

**Expect.** FAIL. The technical result is `INVALID`. The text says a changed message, a different secret, or a wrong tag can cause this, and the app does not say which one.

**Say.**

“I kept the old tag and changed the message. Verification fails. That is what I want if a status message was edited in transit. I should also say the limit: if someone steals the shared secret, they can make a new valid tag. HMAC cannot protect a secret that has already leaked.”

**Concept.** Tamper detection, and the consequence of a stolen secret.

---

## 8. Sign a record and verify it

**Click.** Digital Signatures in the sidebar.

**Click.** Generate key pair. Wait until the public key box fills and the page says 2048-bit.

**Expect.** The private key stays masked until you press Show. You do not need to show it for the demo. If you do, say that it is on screen only for this moment and that the server does not store it.

**Input.** Leave the sign message as `Release candidate 1.4.0`, or type one short sentence.

**Click.** Sign message.

**Expect.** A base64 signature appears. The verify panel receives the same message, the public key, and the signature.

**Click.** Verify signature.

**Expect.** PASS. The technical result is `VALID`.

**Say.**

“This key is RSA-2048. The signature uses RSA-PSS with SHA-256. Only the private key can create it. Anyone with the public key can check it. PASS means this public key accepts the signature over these exact UTF-8 bytes. It becomes the teaching assistant’s signature only if I already know that this public key belongs to the teaching assistant. The app does not have a certificate authority to decide that for me.”

**Concept.** Public-key signatures, and the difference between “valid” and “trusted identity.”

---

## 9. Change the record

**Click.** In the Verify panel, change the message. Add one word, such as `draft`, or change `1.4.0` to `1.4.1`. Click Verify signature.

**Expect.** FAIL. The technical result is `INVALID`.

**Say.**

“The signature was made over the original sentence. One extra word changes the bytes, so the public key rejects it. That is integrity and origin in the cryptographic sense: origin meaning this key, not a person’s legal identity.”

**Concept.** Signatures cover exact bytes. A changed record fails verification.

---

## 10. Open Reports

**Click.** Reports in the sidebar.

**Expect.** The hash, HMAC, and signature operations you just performed are in the table, with times and badges. Hash comparison shows PASS and FAIL. HMAC verification shows PASS and FAIL. The hash you calculated with no reference shows NOT VERIFIED. Key generation and HMAC generation show RECORDED, because they were not verifications. View on one row opens JSON. That JSON has metadata such as a verdict or message length. It does not contain the HMAC secret or the private key.

**Click.** Export CSV only if you want a file. It downloads the filtered history.

**Say.**

“Reports reads the SQLite history. I can filter by operation and status, and I can export CSV. This is an audit of what was checked. It is not a list of malware findings.”

**Concept.** Sanitized audit history.

---

## 11. Close

**Say this.**

“To summarise, CryptoGuard separates three ideas that are often mixed together. A SHA-256 digest checks bytes against a reference I supply. HMAC checks a shared secret. An RSA-PSS signature checks a public key. PASS is a match for that evidence only. The project also has a small provenance record, dependency queries against OSV, and a CycloneDX SBOM, and I can show those if you want. It does not detect malware, it does not manage user accounts, and a valid signature does not automatically prove a real-world identity. Those are the limits I would want an examiner to remember. Thank you. I am happy to take questions.”

**Time.** About 30 seconds.

---

## If you are asked to show one extra module

Pick one, and only if time remains.

**Provenance.** Explain that digest status and signature status are separate, and that this is not SLSA.

**Dependency Scanner.** Upload a real `package.json` with exact versions. Say that packages are not installed. If OSV returns no advisory, say “no match from OSV,” not “this package is safe.” If the network fails, say the source failed.

**SBOM.** Generate from the same manifest. Say it lists declared components and is validated as CycloneDX 1.7. It is not a vulnerability database.

Do not open NVD unless you have enabled it in the backend environment. The default is off. If it is off, say so.

---

## Timing guide

| Stage | Minutes |
| --- | --- |
| Opening and dashboard | 1.0 |
| SHA-256, PASS, and FAIL | 1.5 |
| HMAC generate, PASS, and FAIL | 1.5 |
| Sign, PASS, and changed record | 1.5 |
| Reports and closing | 1.0 |

If you are stopped early, finish on the hash FAIL. That single contrast, NOT VERIFIED then PASS then FAIL, already explains the project.
