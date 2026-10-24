"""Build the CryptoGuard project report and embed captured website screenshots."""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

ROOT = Path(r"c:\Users\kamod\OneDrive\Desktop\CIS-030(Main)")
IMG = ROOT / "report_images"
SHOTS = {
    1: "01-dashboard.png",
    2: "02-sidebar.png",
    3: "03-hash-not-verified.png",
    4: "04-hash-pass.png",
    5: "05-hash-fail.png",
    6: "06-hmac.png",
    7: "07-signatures.png",
    8: "08-reports.png",
    9: "09-provenance.png",
    10: "10-dependencies.png",
    11: "11-sbom.png",
    12: "12-vulnerabilities.png",
    13: "13-sources.png",
    14: "14-documentation.png",
    15: "15-api-docs.png",
}

OUT = r"c:\Users\kamod\OneDrive\Desktop\CIS-030(Main)\CryptoGuard_Project_Report_with_images.docx"
NAVY = RGBColor(0x0B, 0x1F, 0x33)
TEAL = RGBColor(0x0E, 0x74, 0x86)
MUTED = RGBColor(0x4B, 0x55, 0x63)


def font(run, name="Times New Roman", size=12, bold=False, italic=False, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color is not None:
        run.font.color.rgb = color


def body(doc, text, space_after=8, first_line=True):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    if first_line:
        p.paragraph_format.first_line_indent = Cm(1.0)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    font(p.add_run(text))
    return p


def bullet(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1.25)
    p.paragraph_format.first_line_indent = Cm(-0.4)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    font(p.add_run("•  " + text))
    return p


def heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.keep_with_next = True
    size = 16 if level == 1 else 13
    font(p.add_run(text), size=size, bold=True, color=NAVY)
    return p


def caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(12)
    font(p.add_run(text), size=11, italic=True, color=MUTED)
    return p


def shade(cell, hex_color):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tc_pr.append(shd)


def borders(cell, color="0E7486"):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "dashed")
        el.set(qn("w:sz"), "12")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        tc_borders.append(el)
    tc_pr.append(tc_borders)


def row_height(cell, twips):
    tr = cell._tc.getparent()
    tr_pr = tr.get_or_add_trPr()
    tr_height = OxmlElement("w:trHeight")
    tr_height.set(qn("w:val"), str(twips))
    tr_height.set(qn("w:hRule"), "atLeast")
    tr_pr.append(tr_height)


def image_slot(doc, number, page_name, where, what):
    path = IMG / SHOTS[number]
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    if path.exists():
        width = Inches(2.35) if number == 2 else Inches(6.15)
        p.add_run().add_picture(str(path), width=width)
    else:
        font(p.add_run("IMAGE HERE"), size=16, bold=True, color=TEAL)
        missing = doc.add_paragraph()
        missing.alignment = WD_ALIGN_PARAGRAPH.CENTER
        font(missing.add_run(f"{page_name}. {where}"), size=11, italic=True, color=MUTED)
    caption(doc, f"Figure {number}. {what}")


def blank_line(doc, label):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(4)
    font(p.add_run(label), size=13)
    font(p.add_run("  ______________________________"), size=13)


def add_table(doc, headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        shade(cell, "0B1F33")
        run = cell.paragraphs[0].add_run(header)
        font(run, size=11, bold=True, color=RGBColor(255, 255, 255))
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            cell = table.rows[r + 1].cells[c]
            cell.text = ""
            if r % 2 == 1:
                shade(cell, "F4F7F8")
            font(cell.paragraphs[0].add_run(value), size=11)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def footer(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(p.add_run("CryptoGuard  ·  Cryptographic Integrity and Software Supply Chain Verification Platform  ·  "), size=9, color=MUTED)
    run = p.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)
    font(run, size=9, color=MUTED)


def build():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.0)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    footer(section)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")

    # Title page
    for _ in range(2):
        doc.add_paragraph()
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(t.add_run("PROJECT REPORT"), size=14, bold=True, color=TEAL)
    t2 = doc.add_paragraph()
    t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t2.paragraph_format.space_before = Pt(10)
    font(t2.add_run("CryptoGuard"), size=28, bold=True, color=NAVY)
    t3 = doc.add_paragraph()
    t3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(
        t3.add_run("Cryptographic Integrity and Software Supply Chain\nVerification Platform"),
        size=16,
        color=NAVY,
    )
    t4 = doc.add_paragraph()
    t4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t4.paragraph_format.space_before = Pt(8)
    font(t4.add_run("Version 1.0.0"), size=12, italic=True, color=MUTED)
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.paragraph_format.space_before = Pt(16)
    font(
        sub.add_run(
            "A local web application for SHA-256 file integrity,\nHMAC-SHA256 message authentication, and RSA-PSS digital signatures"
        ),
        size=12,
    )
    doc.add_paragraph()
    for label in (
        "Student name",
        "Enrolment number",
        "Programme and department",
        "Guide",
        "Academic year",
    ):
        blank_line(doc, label)
    note = doc.add_paragraph()
    note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    note.paragraph_format.space_before = Pt(18)
    font(
        note.add_run("Fill the blank lines above. Do not invent a company or a funding body."),
        size=11,
        italic=True,
        color=MUTED,
    )
    doc.add_page_break()

    heading(doc, "List of figures", 1)
    body(
        doc,
        "This report is written from the CryptoGuard repository, version 1.0.0. The figures are screenshots of the running website at http://127.0.0.1:3000/ and of the API documentation at http://127.0.0.1:8000/docs. They were captured on 23 October 2026 while the sidebar showed Backend connected and the health check reported API ok and database ok. The hash, HMAC, signature, provenance, dependency, and SBOM figures show results returned by that backend. The private key is masked in the signature figure and is not included in the provenance figure.",
        first_line=False,
    )

    heading(doc, "Abstract", 1)
    body(
        doc,
        "Software is often accepted because a filename or a package name looks familiar. This project builds CryptoGuard, a local full-stack application that separates three checks. The FastAPI backend hashes an uploaded file with SHA-256 and compares it with a reference digest when one is supplied. It creates and checks HMAC-SHA256 tags without writing the shared secret to the database. It generates a 2048-bit RSA key pair and signs or verifies UTF-8 messages with RSA-PSS and SHA-256. The React interface shows PASS, FAIL, or NOT VERIFIED and explains the limit of each result. SQLite stores sanitized history. Additional modules parse package.json and requirements.txt, query the OSV service, optionally query NVD, and emit a CycloneDX 1.7 SBOM. A passed check is limited to the evidence submitted. The system does not detect malware and does not establish a real-world identity by itself.",
    )

    heading(doc, "1. Introduction", 1)
    body(
        doc,
        "Software moves through a supply chain. A publisher prepares a file, a download or a dependency carries it, and a user runs it. Along that path a file can be replaced or edited and still keep the same name. A release message can be changed after it was written. A record can be described as signed without anyone checking which key was used. CryptoGuard is a teaching platform that runs the real checks for those situations and labels what each result does not prove.",
    )
    body(
        doc,
        "A hash, a message authentication code, and a digital signature are different tools. SHA-256 produces a fingerprint of file bytes. HMAC-SHA256 shows that a shared secret authenticates one exact message. RSA-PSS shows that a private key signed one exact text and that the matching public key accepts that signature. Mixing those ideas creates false confidence. A matching hash is not a signature. A valid signature is not proof of a person’s identity. An empty vulnerability search is not proof that software is safe.",
    )
    body(
        doc,
        "The application title shown in the interface, the API, and the database records is CryptoGuard — Cryptographic Integrity and Software Supply Chain Verification Platform. The short name is CryptoGuard. The version in the backend settings and in the frontend package is 1.0.0. The work is an academic minimum viable product that runs on one machine. There are no user accounts. The demonstration path is the dashboard, the hash checker, HMAC, digital signatures, and the reports page.",
    )
    body(
        doc,
        "The benefit of the project is that a student or a small lab team can submit real evidence and read a result produced by the algorithm, not by a sentence typed into the page. The browser collects the file, the message, or the key. Python on the API performs the cryptography. The screen then says PASS, FAIL, or NOT VERIFIED, and the operation is stored so it can be shown again.",
    )
    image_slot(
        doc,
        1,
        "Dashboard  (/)",
        "Open the home page. Include the heading, the tagline, and the sidebar line Backend connected.",
        "Dashboard of the CryptoGuard website. Paste the home-page screenshot in the box above.",
    )

    heading(doc, "2. Problem statement", 1)
    body(
        doc,
        "People treat a familiar download as if it were authenticated. CryptoGuard is built around four practical situations. A distributed file can be modified after it leaves the course page, while the filename stays the same. A download can be compared with a published digest only when that digest is supplied by the user. A release message can be edited after an HMAC tag was created. A signed record can be checked with a public key, and a change in the text makes verification fail.",
    )
    body(
        doc,
        "The same section states what the project does not claim. There is no malware verdict. The application does not automatically trust a reference digest, a shared secret, or a public key. An empty response from OSV is not treated as proof that a package is safe. Provenance in this version is a small signed JSON record. It is not a full SLSA, in-toto, or Sigstore implementation.",
    )

    heading(doc, "3. Objectives", 1)
    heading(doc, "3.1 Implemented objectives", 2)
    for item in (
        "Compute the SHA-256 digest of an uploaded file without executing the file.",
        "Compare that digest with a user-supplied reference and return MATCH or MISMATCH.",
        "Return NOT VERIFIED when a digest is calculated and no reference is supplied.",
        "Generate and verify HMAC-SHA256, including a server-generated secret when the user omits one.",
        "Generate an RSA-2048 key pair, sign UTF-8 text, and verify RSA-PSS signatures.",
        "Present PASS, FAIL, and NOT VERIFIED in the interface, mapped from the backend verdicts.",
        "Persist sanitized history and export it as CSV and JSON.",
        "Keep HMAC secrets and RSA private keys out of that history.",
    ):
        bullet(doc, item)
    heading(doc, "3.2 Supporting modules that are also implemented", 2)
    for item in (
        "Provenance sign and verify for a small canonical JSON record, with digest status kept separate from signature status.",
        "Parsing of npm and Python requirement manifests, live OSV queries, and an optional NVD lookup that is disabled unless configured.",
        "CycloneDX 1.7 SBOM generation, validated against the schema stored in the repository.",
        "Health and source-availability endpoints used by the dashboard and the Datasets & Sources page.",
    ):
        bullet(doc, item)
    heading(doc, "3.3 Not objectives of this version", 2)
    body(
        doc,
        "User accounts, malware scanning, package installation, archive extraction, script execution, and a public production deployment are outside this version. PostgreSQL is a possible later database URL. The tested database is SQLite, and no PostgreSQL driver is installed.",
    )

    heading(doc, "4. Existing situation and proposed system", 1)
    body(
        doc,
        "In the usual lab habit, a person compares files by name, pastes a hash into a generic checksum tool, or reads the word signed without knowing which key was used. Those habits do not record the difference between a digest that was only calculated and a digest that matched a reference. They also do not warn that a valid signature still needs a reason to trust the public key.",
    )
    body(
        doc,
        "CryptoGuard gives each check its own page, a backend implementation of the algorithm, a written limitation, and a history row. The proposed system is this repository. The comparison below describes behaviour that is implemented, not a product that was only drawn.",
    )
    add_table(
        doc,
        ["Question", "Typical manual habit", "CryptoGuard behaviour"],
        [
            ["Was the file hashed?", "A local checksum tool, often with no record", "SHA-256 on the server, and a history row is stored"],
            ["Was it compared?", "The comparison is easy to forget", "No reference produces NOT VERIFIED"],
            ["Was a message authenticated?", "Often confused with a hash", "HMAC-SHA256. The secret is not stored"],
            ["Was a record signed?", "Signed, with no algorithm named", "RSA-2048 PSS with SHA-256. The private key is not stored"],
        ],
    )

    heading(doc, "5. Requirements", 1)
    heading(doc, "5.1 Functional requirements", 2)
    for item in (
        "Upload a file up to 10 MB and obtain its SHA-256 digest.",
        "Accept an optional reference digest of 64 hexadecimal characters, with an optional sha256: prefix.",
        "Generate and verify HMAC-SHA256 over UTF-8 text.",
        "Generate RSA keys and sign or verify UTF-8 text.",
        "Show a distinct result for a match, a mismatch, and a hash calculated with no reference.",
        "List, filter, export, and delete history.",
        "Parse package.json and requirements.txt, query OSV for exact versions, and generate a schema-checked SBOM.",
    ):
        bullet(doc, item)
    heading(doc, "5.2 Non-functional requirements", 2)
    for item in (
        "Cryptography runs on the backend. The browser does not invent MATCH or MISMATCH.",
        "Secrets are not written to the verification_records table.",
        "Files are read in 64 KiB chunks and are not executed. Filenames are reduced to a safe base name.",
        "API errors stay visible. A failed call is not replaced with a successful placeholder.",
        "The interface states the limit of a passed check.",
    ):
        bullet(doc, item)
    heading(doc, "5.3 Environment", 2)
    body(
        doc,
        "The local run needs Python 3.11 or newer, Node.js and npm, and a browser. This workspace was exercised with Python 3.13. Network access is required only when OSV, NVD, or a remote CycloneDX schema status check is used. Hashing, HMAC, signatures, provenance, SBOM generation, and OSV do not need an API key. NVD can use a key, and NVD lookups stay disabled until NVD_ENABLED is set.",
    )

    heading(doc, "6. Technology stack", 1)
    body(
        doc,
        "The backend language is Python. Hashing, HMAC, signatures, manifest parsing, HTTP calls to vulnerability sources, and database access are Python modules under backend/app. FastAPI exposes each check as an HTTP route and publishes OpenAPI documentation. Uvicorn is the ASGI server. The command npm run dev inside the backend folder starts Uvicorn. It does not start a Node API. The documented bind address is 127.0.0.1 port 8000. Pydantic checks JSON request bodies, and pydantic-settings reads the optional environment file. A short HMAC tag is rejected before it is treated as a verification result.",
    )
    body(
        doc,
        "The frontend language is TypeScript. React 18 renders the pages and holds form state. React Router selects the page. Vite serves the development site, configured for 127.0.0.1 port 3000, and proxies /api to the backend when VITE_API_BASE_URL is unset. Tailwind CSS styles the navy layout, forms, tables, and badges. Axios, in frontend/src/services/api.ts, makes every browser call. If the API is stopped, Axios does not invent a PASS result. Lucide React supplies sidebar icons. Recharts draws the 14-day activity chart only from counts returned by the dashboard API.",
    )
    body(
        doc,
        "SHA-256 uses hashlib. HMAC-SHA256 and constant-time comparison use the hmac module, including hmac.compare_digest. A generated HMAC secret uses secrets.token_hex. RSA key generation and RSA-PSS use the cryptography package: 2048-bit keys, public exponent 65537, MGF1 with SHA-256, and a salt length equal to the digest length. The algorithm name stored by the signature service is RSA-2048-PSS-SHA256. Private keys are returned as unencrypted PEM and are not written to SQLite.",
    )
    body(
        doc,
        "SQLAlchemy creates and queries three SQLite tables: verification_records, vulnerability_lookup_cache, and data_source_checks. The default database file is backend/data/cryptoguard.db. HTTPX performs the OSV query, the optional NVD query, and the schema status check. jsonschema validates a generated SBOM against the CycloneDX 1.7 schema shipped at backend/app/data/bom-1.7.schema.json. python-multipart lets FastAPI read file uploads. pytest tests the backend. Vitest, React Testing Library, and jsdom test the frontend. Django, Flask, Angular, Next.js, MongoDB, Redis, and a malware-scanning SDK are not dependencies of this project.",
    )
    image_slot(
        doc,
        2,
        "Any inner page, with the sidebar open",
        "Open the menu if the sidebar is hidden. Show the module names: Dashboard, Hash Checker, HMAC, Digital Signatures, Provenance, Dependencies, SBOM, Vulnerabilities, Sources, and Reports.",
        "Website navigation. Paste a screenshot that shows the CryptoGuard sidebar.",
    )

    heading(doc, "7. System architecture", 1)
    body(
        doc,
        "The browser shows forms, result badges, limitation text, and downloads of JSON that the API returned. The API layer in backend/app/api/routes.py validates input and chooses a service. Services own the work: integrity.py, hmac_service.py, signatures.py, and the supply-chain services for provenance, manifests, OSV, NVD, and SBOMs. SQLite stores sanitized history, a short-lived vulnerability cache, and source-check rows.",
    )
    body(
        doc,
        "A hash comparison follows a concrete path. IntegrityPage calls verifyFile in the frontend API client. That function posts the file and the reference digest to /api/integrity/verify. The route streams the upload through read_upload_hashed, compares the digest in the integrity service, and records the operation with save_operation. MATCH is shown as PASS. MISMATCH is shown as FAIL. A hash with no reference remains NOT VERIFIED. That path is the architecture evidence. The screenshots below should be taken after performing the check, not drawn by hand.",
    )
    image_slot(
        doc,
        3,
        "Hash Checker  (/integrity)  — result NOT VERIFIED",
        "Upload a small text file, leave Reference digest empty, and click Calculate SHA-256. The badge must say NOT VERIFIED.",
        "Hash calculation without a reference. Paste that Hash Checker screenshot in the box above.",
    )
    image_slot(
        doc,
        4,
        "Hash Checker  (/integrity)  — result PASS",
        "Copy the digest from the previous result, paste it into Reference digest, and click Compare Hashes. The badge must say PASS.",
        "Matching SHA-256 comparison. Paste the PASS screenshot in the box above.",
    )
    image_slot(
        doc,
        5,
        "Hash Checker  (/integrity)  — result FAIL",
        "Change one character of the reference digest and compare again. The badge must say FAIL.",
        "Mismatched SHA-256 comparison. Paste the FAIL screenshot in the box above.",
    )

    heading(doc, "8. Methodology", 1)
    body(
        doc,
        "The build order follows the need to keep each result honest. The result vocabulary was defined first: match, mismatch, not verified, valid, and invalid. SHA-256 streaming and constant-time digest comparison were implemented next. HMAC was added without persisting the secret. RSA-PSS was added with an explicit key size, public exponent, and padding. Sanitized history was stored after those checks existed. React pages were then mapped onto the backend verdicts, so MATCH and VALID become PASS, MISMATCH and INVALID become FAIL, and a hash without a reference stays NOT VERIFIED.",
    )
    body(
        doc,
        "Provenance, OSV lookup, and SBOM generation were added as separate modules, each with its own limitation text. Tests cover the cryptography and the rule that an empty OSV body is not proof of safety. This is a construction method. It is not a user study, and this report does not invent survey results, timing scores, or accuracy percentages.",
    )

    heading(doc, "9. Implementation", 1)
    heading(doc, "9.1 File integrity", 2)
    body(
        doc,
        "File hashing is implemented in backend/app/utils/files.py and backend/app/services/integrity.py. The page is frontend/src/pages/IntegrityPage.tsx. The server reads the upload in chunks of 64 KiB, updates hashlib.sha256, and discards the chunks. The local upload limit is 10 MB. The file is not executed. A path such as ..\\secret.txt is reduced to a base name. If no reference is sent, the operation type is hash and the verdict is NOT VERIFIED. If a reference is sent, the operation type is hash_verify. The reference may begin with sha256:. It must be 64 hexadecimal characters after that prefix is removed. Comparison uses hmac.compare_digest. PASS means the bytes match the reference that was typed. It does not name the publisher, and it does not mean the file is free of malware.",
    )
    heading(doc, "9.2 HMAC authentication", 2)
    body(
        doc,
        "HMAC is implemented in backend/app/services/hmac_service.py. The routes are hmac generate and hmac verify. The page is frontend/src/pages/HmacPage.tsx. The message and the secret are encoded as UTF-8. The tag is the hex digest of HMAC-SHA256. If the secret is omitted, secrets.token_hex(32) creates a 32-byte secret, shown as 64 hex characters. A blank secret is rejected. Verification compares the expected tag and the submitted tag with hmac.compare_digest. VALID becomes PASS and INVALID becomes FAIL. The application does not say which of the message, the secret, or the tag was wrong. The secret and the tag are returned so the user can verify them, and they are not fields in the stored history. The downloadable tag report contains the message, the tag, and the algorithm name, not the secret.",
    )
    image_slot(
        doc,
        6,
        "HMAC Verifier  (/hmac)",
        "Enter a short message, generate a tag, then verify the same message, secret, and tag. Show the PASS badge. Optionally take a second shot after changing one word so the badge says FAIL, and paste the clearer of the two, or both if they fit.",
        "HMAC-SHA256 result on the website. Paste the HMAC page screenshot in the box above.",
    )
    heading(doc, "9.3 Digital signatures", 2)
    body(
        doc,
        "Signatures are implemented in backend/app/services/signatures.py. The page is frontend/src/pages/SignaturePage.tsx. Key generation uses rsa.generate_private_key with public exponent 65537 and key size 2048. Signing and verification use RSA-PSS, MGF1 with SHA-256, salt length equal to the SHA-256 digest length, and SHA-256 as the message hash. The signature is returned as base64. The private key is returned once as unencrypted PKCS#8 PEM and is not stored. History may store the key size or a SHA-256 fingerprint of the public-key PEM. That fingerprint is not a person’s identity. PASS means this public key accepts these exact UTF-8 bytes.",
    )
    image_slot(
        doc,
        7,
        "Digital Signatures  (/signatures)",
        "Generate a key pair, sign a short sentence, then verify it with the matching public key. The badge should say PASS. Keep the private key out of a screenshot you will submit if the page shows the full PEM. Crop to the result badge if needed.",
        "RSA-PSS signature check on the website. Paste the Digital Signatures screenshot in the box above.",
    )
    heading(doc, "9.4 History and reports", 2)
    body(
        doc,
        "Each completed check can create a row in verification_records through backend/app/services/history.py. The stored fields include the operation type, status, algorithm, filename, size, digest when relevant, and a short metadata object. The Reports page, at /history and /reports, lists those rows, filters them on the server, exports CSV, and can open a JSON report. Deleting history removes stored rows. Dashboard counts and the activity chart are read from this table. They are not numbers typed into the page.",
    )
    image_slot(
        doc,
        8,
        "Reports  (/history)",
        "Open Reports after the hash, HMAC, and signature checks. The table should show those real operations. Include the operation type and the status.",
        "Verification history stored by CryptoGuard. Paste the Reports screenshot in the box above.",
    )
    heading(doc, "9.5 Supply-chain modules", 2)
    body(
        doc,
        "Provenance signing and verification use a small canonical JSON record. Digest status and signature status are stored and shown separately, so a matching file digest is not presented as a valid signature. The dependency scanner reads package.json and requirements.txt without installing packages. Exact versions can be sent to the public OSV API. The vulnerability page can also ask NVD about a CVE identifier, but that lookup is off unless nvd_enabled is true. The default in config.py is false. The SBOM generator emits CycloneDX 1.7 JSON and validates it against the schema file in the repository. Licences and transitive dependencies are not invented.",
    )
    image_slot(
        doc,
        9,
        "Provenance  (/provenance)",
        "Open the Provenance page. If you complete a sign or verify action, include the separate digest status and signature status.",
        "Provenance page of the website. Paste the screenshot in the box above.",
    )
    image_slot(
        doc,
        10,
        "Dependency Scanner  (/dependencies)",
        "Open the Dependency Scanner. A result screenshot is appropriate only after you upload a real package.json or requirements.txt from this project.",
        "Dependency Scanner page. Paste the website screenshot in the box above.",
    )
    image_slot(
        doc,
        11,
        "SBOM Generator  (/sbom)",
        "Open the SBOM page. If you generate a document, include the note that it is CycloneDX JSON checked against the schema.",
        "SBOM Generator page. Paste the website screenshot in the box above.",
    )
    image_slot(
        doc,
        12,
        "Vulnerability Intelligence  (/vulnerabilities)",
        "Open the page. The NVD checkbox should show that NVD is disabled until NVD_ENABLED is true. Query OSV only if the network is available. If OSV does not answer, do not describe that as a safe package.",
        "Vulnerability Intelligence page. Paste the website screenshot in the box above.",
    )
    image_slot(
        doc,
        13,
        "Datasets & Sources  (/sources)",
        "Open Datasets & Sources. Show the source cards and the fact that availability is not a security result.",
        "Datasets and Sources page. Paste the website screenshot in the box above.",
    )
    heading(doc, "9.6 Interface", 2)
    body(
        doc,
        "The dashboard introduces the three checks, explains PASS, FAIL, and NOT VERIFIED, and shows system health from /api/health. The sidebar repeats a short health line on every page: API status and database status. That line is a connection check. It is not a threat level. In-app documentation restates the limits of each module so a reader can see them without leaving the site. Charts use database counts. An empty database shows an empty state rather than a fabricated chart.",
    )
    image_slot(
        doc,
        14,
        "Documentation  (/documentation)",
        "Open the in-app documentation page and capture the part that explains what PASS does not prove.",
        "In-app documentation. Paste the website screenshot in the box above.",
    )
    image_slot(
        doc,
        15,
        "FastAPI documentation  (http://127.0.0.1:8000/docs)",
        "Open the API docs in the browser. Show the groups for integrity, HMAC, and signatures.",
        "Interactive API documentation. Paste that browser screenshot in the box above.",
    )

    heading(doc, "10. Testing and results", 1)
    body(
        doc,
        "Results in this section come from the tests that exist in the repository. This report does not invent a pass rate, a throughput number, or a malware sample.",
    )
    heading(doc, "10.1 Backend tests", 2)
    for item in (
        "An empty file hashes to the standard SHA-256 test vector and is NOT VERIFIED when no reference is sent. That vector belongs to the empty file only. It is not the digest of a demo file.",
        "A matching reference, including a different letter case, is MATCH. A different digest is not a match.",
        "An invalid reference is rejected. An upload over the configured limit is rejected. Directory prefixes are removed from filenames.",
        "HMAC verification fails when the message is tampered with. The HMAC secret and tag are not stored on the history row.",
        "Signatures verify with the matching key, fail with the wrong material, and reject malformed input.",
        "History can be exported and deleted. Dashboard counts come from stored rows. The health endpoint checks the database.",
        "SBOM output validates against the CycloneDX 1.7 schema in the tree.",
        "An empty OSV body is not treated as proof of safety.",
        "Provenance can show a missing digest or a missing signature, and a signed record can match an uploaded artifact.",
    ):
        bullet(doc, item)
    heading(doc, "10.2 Frontend tests", 2)
    for item in (
        "Navigation links point at the real routes.",
        "An empty dashboard state is shown when the stats API returns zero operations.",
        "Hash Checker requires a file, shows a loading state, then shows PASS for a MATCH response, and shows an API error when the request fails.",
        "Short digests and short HMAC tags are rejected in the form helpers.",
        "Source cards render the status returned by the API.",
    ):
        bullet(doc, item)
    body(
        doc,
        "An input error, such as a short digest, is HTTP 400. It is not a cryptographic FAIL. A stopped API is a connection failure. It is also not a cryptographic FAIL. Those distinctions are part of the result, because they stop a demo from calling every red message a failed signature.",
    )

    heading(doc, "11. Security considerations", 1)
    for item in (
        "SHA-256 equality is a byte comparison. Trust in the result still depends on trust in the reference digest that the user pasted.",
        "Digests and HMAC tags are compared with hmac.compare_digest so the comparison does not stop at the first different character.",
        "An omitted HMAC secret is generated with secrets.token_hex. The secret is omitted from the history row.",
        "The RSA private key is returned once, as unencrypted PEM, and is not stored. A copy in a chat or in a screenshot is still a real key, so submitted figures should not include a full private key.",
        "A public-key fingerprint identifies PEM text. It does not identify a person.",
        "Uploads have a size limit, are read in chunks, are not executed, and have cleaned filenames.",
        "HTTP 400, a connection failure, and a cryptographic FAIL are handled separately in the interface.",
        "OSV and NVD failures are source failures. The vulnerability cache expiry defaults to six hours.",
        "There is no authentication layer in front of the local API. The application is intended for one machine.",
    ):
        bullet(doc, item)

    heading(doc, "12. Limitations", 1)
    body(
        doc,
        "The useful claim of CryptoGuard is small, and the limitations are part of that claim. A reference digest is trusted only because the user chose its source. The HMAC secret must be shared outside the application and must stay secret. The public key is trusted only if the user has a reason to trust it. The project does not detect malware. Provenance is not SLSA or Sigstore compliance. The deployment is a single-user local application. NVD lookup exists and remains disabled unless it is configured. Enabling it is a configuration change, not a new algorithm.",
    )

    heading(doc, "13. Future scope", 1)
    body(
        doc,
        "Later work can add labels for trusted public keys, encrypted or externally held private keys, access control, and a hardened deployment. A fuller build-attestation format belongs in a later course if that course covers it. Broader automated end-to-end tests can be added around the pages. OSV lookup and CycloneDX export are already present, so they are not listed here as future fiction. NVD is already implemented and disabled by default.",
    )

    heading(doc, "14. Conclusion", 1)
    body(
        doc,
        "CryptoGuard demonstrates file integrity, message authentication, and digital signatures as three different checks. It records the checks, withholds secrets from that record, and states what a passed result does not prove. The React and TypeScript website collects the evidence. The Python and FastAPI backend performs SHA-256, HMAC-SHA256, and RSA-PSS. SQLite keeps the sanitized history that the dashboard and the reports page display. That separation, and the honesty of PASS, FAIL, and NOT VERIFIED, is the cybersecurity lesson of the project.",
    )

    heading(doc, "15. References", 1)
    refs = [
        "NIST FIPS 180-4, Secure Hash Standard (SHA-256). https://csrc.nist.gov/publications/detail/fips/180/4/final",
        "NIST FIPS 198-1, The Keyed-Hash Message Authentication Code (HMAC). https://csrc.nist.gov/publications/detail/fips/198/1/final",
        "RFC 8017, PKCS #1: RSA Cryptography Specifications, including RSASSA-PSS. https://www.rfc-editor.org/rfc/rfc8017",
        "Python documentation for hashlib, hmac, and secrets. https://docs.python.org/3/library/hmac.html",
        "The cryptography library, RSA-PSS. https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/",
        "FastAPI documentation. https://fastapi.tiangolo.com/",
        "OSV API documentation. https://google.github.io/osv.dev/api/",
        "NVD vulnerability API, for the optional module. https://nvd.nist.gov/developers/vulnerabilities",
        "CycloneDX 1.7 JSON specification. https://cyclonedx.org/docs/1.7/json/",
    ]
    for i, ref in enumerate(refs, 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.75)
        p.paragraph_format.first_line_indent = Cm(-0.75)
        p.paragraph_format.space_after = Pt(4)
        font(p.add_run(f"[{i}]  {ref}"), size=12)

    heading(doc, "Appendix A. Screenshot checklist", 1)
    body(
        doc,
        "These are the screenshots already placed in the report. The figure number matches the caption under each image.",
        first_line=False,
    )
    checklist = [
        "Figure 1 — Dashboard home page, with Backend connected.",
        "Figure 2 — Sidebar showing the module names.",
        "Figure 3 — Hash Checker, badge NOT VERIFIED, reference left empty.",
        "Figure 4 — Hash Checker, badge PASS, after pasting the same digest.",
        "Figure 5 — Hash Checker, badge FAIL, after changing the reference.",
        "Figure 6 — HMAC Verifier, with a PASS or FAIL badge from a real tag.",
        "Figure 7 — Digital Signatures, with a PASS badge. Do not include a full private key.",
        "Figure 8 — Reports, showing the operations just performed.",
        "Figure 9 — Provenance page.",
        "Figure 10 — Dependency Scanner page.",
        "Figure 11 — SBOM Generator page.",
        "Figure 12 — Vulnerability Intelligence page.",
        "Figure 13 — Datasets & Sources page.",
        "Figure 14 — In-app documentation page.",
        "Figure 15 — FastAPI page at http://127.0.0.1:8000/docs.",
    ]
    for item in checklist:
        bullet(doc, item)

    heading(doc, "Appendix B. Local addresses", 1)
    for item in (
        "Website: http://127.0.0.1:3000/  (the Vite terminal prints the exact address if another port is already in use).",
        "API health: http://127.0.0.1:8000/api/health",
        "API documentation: http://127.0.0.1:8000/docs",
        "Start the API from the backend folder with npm run dev.",
        "Start the website from the frontend folder with npm run dev.",
    ):
        bullet(doc, item)

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
