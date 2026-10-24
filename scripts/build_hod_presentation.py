"""Build CryptoGuard_HOD_Presentation.pptx from the audited implementation.

Run from the repository root:

    backend\\.venv\\Scripts\\python.exe scripts\\build_hod_presentation.py
"""

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

BG = RGBColor(0x0B, 0x12, 0x20)
CARD = RGBColor(0x15, 0x20, 0x34)
CARD_ALT = RGBColor(0x1A, 0x28, 0x40)
LINE = RGBColor(0x2C, 0x3E, 0x5A)
CYAN = RGBColor(0x4C, 0xC9, 0xF0)
BLUE = RGBColor(0x7D, 0xB7, 0xFF)
TEXT = RGBColor(0xF4, 0xF7, 0xFB)
MUTED = RGBColor(0xC5, 0xD2, 0xE4)
DIM = RGBColor(0x8E, 0xA2, 0xBB)
GREEN = RGBColor(0x3D, 0xDC, 0x97)
RED = RGBColor(0xFF, 0x7B, 0x86)
AMBER = RGBColor(0xF5, 0xC1, 0x6C)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

W = 13.333
H = 7.5


def rgb_hex(color: RGBColor) -> str:
    return f"{color[0]:02X}{color[1]:02X}{color[2]:02X}"


def set_run(run, size, color, bold=False, font="Calibri"):
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = font
    run.font.italic = False


def add_text(slide, x, y, w, h, text, size=16, color=TEXT, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=2):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.vertical_anchor = anchor
    for margin in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, margin, Emu(0))
    lines = str(text).split("\n")
    for index, line in enumerate(lines):
        paragraph = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
        paragraph.alignment = align
        paragraph.space_before = Pt(0)
        paragraph.space_after = Pt(spacing)
        run = paragraph.add_run()
        run.text = line
        set_run(run, size, color, bold)
    return box


def rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08):
    item = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    item.fill.solid()
    item.fill.fore_color.rgb = fill
    if line is None:
        item.line.fill.background()
    else:
        item.line.color.rgb = line
        item.line.width = Pt(1.0)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            item.adjustments[0] = radius
        except Exception:
            pass
    # Kill any theme shadow that makes text look muddy on a projector.
    effect = item._element.find(qn("a:effectLst"))
    if effect is not None:
        item._element.remove(effect)
    return item


def shade_cell(cell, fill):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    for child in list(tc_pr):
        if child.tag == qn("a:solidFill"):
            tc_pr.remove(child)
    solid = tc_pr.makeelement(qn("a:solidFill"), {})
    color = solid.makeelement(qn("a:srgbClr"), {"val": rgb_hex(fill)})
    solid.append(color)
    tc_pr.append(solid)


def write_cell(cell, text, size, color, bold=False, align=PP_ALIGN.LEFT, fill=CARD):
    cell.text = ""
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.margin_left = Inches(0.08)
    cell.margin_right = Inches(0.08)
    cell.margin_top = Inches(0.04)
    cell.margin_bottom = Inches(0.04)
    shade_cell(cell, fill)
    frame = cell.text_frame
    frame.word_wrap = True
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = text
    set_run(run, size, color, bold)


class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width = Inches(W)
        self.prs.slide_height = Inches(H)
        self.prs.core_properties.title = "CryptoGuard — HOD Presentation"
        self.prs.core_properties.subject = "Hash Functions, Message Authentication and Digital Signatures"
        self.prs.core_properties.category = "Academic presentation"
        self.blank = self.prs.slide_layouts[6]
        self.number = 0

    def add(self, notes: str):
        slide = self.prs.slides.add_slide(self.blank)
        self.number += 1
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = BG
        rect(slide, 0, 0, 0.08, H, CYAN, shape=MSO_SHAPE.RECTANGLE)
        slide.notes_slide.notes_text_frame.text = notes.strip()
        return slide

    def footer(self, slide, section: str):
        add_text(slide, 0.38, 7.14, 10.2, 0.26, f"CryptoGuard   ·   {section}", 12, DIM)
        add_text(slide, 11.5, 7.14, 1.45, 0.26, str(self.number), 12, DIM, align=PP_ALIGN.RIGHT)

    def kicker(self, slide, text):
        add_text(slide, 0.42, 0.26, 10, 0.28, text.upper(), 12, CYAN, True)

    def title(self, slide, text):
        add_text(slide, 0.42, 0.52, 12.4, 0.48, text, 30, WHITE, True)

    def save(self, path: str):
        self.prs.save(path)


def card_copy(slide, x, y, w, h, kicker, title, body, accent=CYAN):
    rect(slide, x, y, w, h, CARD, LINE)
    rect(slide, x, y, 0.07, h, accent, shape=MSO_SHAPE.RECTANGLE)
    add_text(slide, x + 0.22, y + 0.14, w - 0.36, 0.24, kicker.upper(), 11, accent, True)
    add_text(slide, x + 0.22, y + 0.38, w - 0.36, 0.42, title, 16, WHITE, True)
    add_text(slide, x + 0.22, y + 0.86, w - 0.36, h - 1.02, body, 14, MUTED, spacing=4)


def build() -> Presentation:
    deck = Deck()

    # 1 Title
    s = deck.add(
        """Good morning. I am presenting CryptoGuard, a software supply-chain integrity framework for this advanced module on hash functions, message authentication, and digital signatures.
CryptoGuard does not treat a familiar filename as proof. It calculates a real SHA-256 digest, checks an HMAC-SHA256 tag, and verifies an RSA-PSS signature. Each result is labeled with what it proves, and with what it does not prove.
Please replace the placeholders on this slide with our institution, my name, my roll number, the guide’s name, and the academic year before the presentation."""
    )
    add_text(s, 0.48, 0.42, 11, 0.28, "ADVANCED LEVEL  ·  HASH FUNCTIONS, MESSAGE AUTHENTICATION AND DIGITAL SIGNATURES", 13, CYAN, True)
    add_text(s, 0.48, 1.35, 12, 0.82, "CryptoGuard", 54, WHITE, True)
    add_text(s, 0.48, 2.25, 11.5, 0.7, "Software Supply Chain Integrity Verification Framework", 26, BLUE, True)
    add_text(s, 0.48, 3.15, 10.5, 0.4, "Verify integrity.  Authenticate messages.  Check digital signatures.", 18, MUTED)
    labels = [
        ("Institution", "[Institution name]"),
        ("Student", "[Student name, roll number]"),
        ("Guide", "[Guide name]"),
        ("Academic year", "[Academic year]"),
    ]
    for index, (label, value) in enumerate(labels):
        x = 0.48 + index * 3.15
        rect(s, x, 4.35, 2.98, 1.15, CARD, LINE)
        add_text(s, x + 0.16, 4.48, 2.66, 0.24, label.upper(), 11, CYAN, True)
        add_text(s, x + 0.16, 4.78, 2.66, 0.52, value, 14, WHITE, True)
    add_text(
        s,
        0.48,
        5.75,
        12.2,
        0.7,
        "Implemented product name in the application:\nCryptoGuard — Cryptographic Integrity and Software Supply Chain Verification Platform",
        14,
        DIM,
    )
    add_text(s, 0.48, 6.85, 12, 0.28, "Local academic MVP   ·   React frontend   ·   FastAPI backend   ·   SQLite history", 14, MUTED)

    # 2 Problem
    s = deck.add(
        """Imagine a company receives a vendor update. The file is named harborline-agent-1.4.0.zip. The name is familiar, so someone may install it.
A filename is only a label. It does not describe the bytes. If the file changed on the way, the name can still look correct.
CryptoGuard’s first job is to make that difference visible: calculate the SHA-256 digest of the received file and compare it with a reference taken from a channel the receiver already trusts."""
    )
    deck.kicker(s, "The real problem")
    deck.title(s, "A familiar filename is not integrity")
    rect(s, 0.42, 1.35, 7.55, 5.45, CARD, LINE)
    add_text(s, 0.66, 1.52, 7.1, 0.28, "HYPOTHETICAL RELEASE", 12, CYAN, True)
    add_text(s, 0.66, 1.86, 7.1, 0.7, "The download is named\nharborline-agent-1.4.0.zip", 22, WHITE, True)
    add_text(
        s,
        0.66,
        2.85,
        7.05,
        2.3,
        "The receiver expects that release.\nThe name matches the announcement.\nThe bytes may still have changed in transit,\non a mirror, or on a shared drive.",
        16,
        MUTED,
        spacing=6,
    )
    add_text(s, 0.66, 5.45, 7.05, 1.05, "The question is not “Does the name look right?”\nThe question is “Do these bytes match a trusted reference?”", 16, WHITE, True, spacing=4)
    rect(s, 8.2, 1.35, 4.7, 2.5, CARD, LINE)
    add_text(s, 8.42, 1.52, 4.3, 0.26, "FILENAME", 12, AMBER, True)
    add_text(s, 8.42, 1.9, 4.3, 1.6, "Easy to recognize.\nEasy to reuse.\nSays nothing about the file contents.", 16, MUTED, spacing=4)
    rect(s, 8.2, 4.05, 4.7, 2.75, CARD, LINE)
    add_text(s, 8.42, 4.22, 4.3, 0.26, "SHA-256 DIGEST", 12, GREEN, True)
    add_text(s, 8.42, 4.58, 4.3, 1.9, "A fingerprint of the exact bytes.\nUseful only when compared with a reference from a trusted source.", 16, MUTED, spacing=4)
    deck.footer(s, "Problem")

    # 3 Objectives
    s = deck.add(
        """The precise problem is that a hash, a message authentication code, and a digital signature are often treated as the same kind of trust.
CryptoGuard separates them. The current application implements file hashing, HMAC, RSA-PSS signatures, a small provenance record, manifest parsing, live OSV queries, CycloneDX SBOMs, and local history.
It does not implement accounts, malware detection, or a full SLSA attestation system. Those belong in future work, not in today’s claim."""
    )
    deck.kicker(s, "Problem statement and objectives")
    deck.title(s, "Separate the evidence from the claim")
    rect(s, 0.42, 1.28, 6.25, 2.35, CARD, LINE)
    add_text(s, 0.64, 1.42, 5.9, 0.24, "PROBLEM", 12, CYAN, True)
    add_text(s, 0.64, 1.74, 5.85, 1.65, "A matching name, a digest, a tag, and a signature answer different questions. Mixing them creates false confidence.", 16, MUTED)
    rect(s, 6.85, 1.28, 6.05, 2.35, CARD, LINE)
    add_text(s, 7.07, 1.42, 5.65, 0.24, "SOLUTION", 12, CYAN, True)
    add_text(s, 7.07, 1.74, 5.6, 1.65, "Run the real algorithms in a local web application, then state the limit of each result on screen.", 16, MUTED)
    objectives = [
        ("01", "Compare a file with a trusted SHA-256 reference."),
        ("02", "Create and check HMAC-SHA256 without storing the secret."),
        ("03", "Sign and verify UTF-8 text with RSA-2048 and RSA-PSS."),
        ("04", "Record sanitized history and keep supply-chain lookups separate."),
    ]
    for index, (num, text) in enumerate(objectives):
        y = 3.82 + index * 0.75
        rect(s, 0.42, y, 8.35, 0.66, CARD, LINE, radius=0.12)
        add_text(s, 0.58, y + 0.16, 0.6, 0.34, num, 14, CYAN, True)
        add_text(s, 1.25, y + 0.16, 7.3, 0.36, text, 15, WHITE)
    rect(s, 8.95, 3.82, 3.95, 2.91, CARD_ALT, LINE)
    add_text(s, 9.15, 3.98, 3.55, 0.24, "SCOPE TODAY", 12, GREEN, True)
    add_text(s, 9.15, 4.32, 3.55, 1.0, "Local academic MVP.\nNo user accounts.\nNo package installation.", 14, MUTED, spacing=2)
    add_text(s, 9.15, 5.4, 3.55, 0.24, "NOT CLAIMED", 12, AMBER, True)
    add_text(s, 9.15, 5.72, 3.55, 0.8, "Full SLSA, Sigstore, or malware detection.", 14, MUTED)
    deck.footer(s, "Objectives")

    # 4 Three methods
    s = deck.add(
        """A hash, an HMAC, and a signature are not three ways of saying the same thing.
SHA-256 detects a change in bytes if you already have a trusted reference. Anyone can recompute it. It has no key.
HMAC-SHA256 shows that someone who knows the shared secret produced the tag. It does not give public identity, and it does not give non-repudiation, because both sides know the secret.
RSA-PSS lets a private key sign and a public key verify. CryptoGuard can show that this public key accepts this signature. It can name a person only when that public key is trusted for a separate reason."""
    )
    deck.kicker(s, "Why three cryptographic methods?")
    deck.title(s, "Three checks, three different questions")
    headers = ["Question", "SHA-256", "HMAC-SHA256", "RSA-PSS"]
    rows = [
        ["What is checked?", "Exact file bytes", "Message plus shared secret", "Exact UTF-8 bytes"],
        ["Who can verify?", "Anyone with the reference", "Anyone with the secret", "Anyone with the public key"],
        ["Key material", "None", "Shared secret", "Private key signs"],
        ["Identity?", "No", "No", "Only if the key is trusted"],
        ["CryptoGuard stores", "Digest, not the file", "Neither secret nor tag", "Not the private key"],
    ]
    table_shape = s.shapes.add_table(6, 4, Inches(0.42), Inches(1.35), Inches(12.5), Inches(4.85))
    table = table_shape.table
    widths = [2.7, 3.15, 3.35, 3.3]
    for index, width in enumerate(widths):
        table.columns[index].width = Inches(width)
    fills = [CARD_ALT, RGBColor(0x12, 0x32, 0x3A), RGBColor(0x14, 0x2A, 0x48), RGBColor(0x28, 0x22, 0x48)]
    for col, header in enumerate(headers):
        write_cell(table.cell(0, col), header, 14, WHITE, True, fill=fills[col])
        table.rows[0].height = Inches(0.58)
    for r, row in enumerate(rows, start=1):
        table.rows[r].height = Inches(0.7)
        for c, value in enumerate(row):
            write_cell(table.cell(r, c), value, 14, WHITE if c else CYAN, c == 0, fill=CARD if r % 2 else CARD_ALT)
    add_text(s, 0.42, 6.35, 12.4, 0.55, "A passing result answers only the row that was tested. It is not a general certificate of software safety.", 15, MUTED)
    deck.footer(s, "Comparison")

    # 5 Architecture
    s = deck.add(
        """The browser is a React and TypeScript application served by Vite. Axios calls the API. In development, Vite can proxy /api to 127.0.0.1 port 8000.
The backend is FastAPI on Uvicorn. Routes in backend/app/api/routes.py call services. Hashing is in integrity.py and files.py. HMAC is in hmac_service.py. RSA-PSS is in signatures.py.
SQLAlchemy stores sanitized history in SQLite. OSV is a live external query. NVD is implemented but disabled unless NVD_ENABLED is true. CycloneDX validation uses the schema file shipped in the repository."""
    )
    deck.kicker(s, "System architecture")
    deck.title(s, "What the running application actually does")
    nodes = [
        ("Browser", "User"),
        ("React + Vite", "TypeScript UI"),
        ("FastAPI", "Uvicorn  ·  /api"),
        ("Services", "Hash, HMAC, RSA-PSS"),
    ]
    for index, (title, body) in enumerate(nodes):
        x = 0.42 + index * 3.22
        rect(s, x, 1.35, 2.85, 1.35, CARD, LINE)
        add_text(s, x + 0.16, 1.5, 2.55, 0.4, title, 16, WHITE, True)
        add_text(s, x + 0.16, 1.98, 2.55, 0.45, body, 13, MUTED)
        if index < 3:
            add_text(s, x + 2.72, 1.75, 0.5, 0.4, "›", 22, CYAN, True, PP_ALIGN.CENTER)
    stores = [
        ("SQLite", "verification_records\nvulnerability cache\nsource checks", CYAN),
        ("OSV", "Live query for an exact\npackage version. Empty is\nnot called safe.", GREEN),
        ("NVD", "Optional CVE lookup.\nOff unless NVD_ENABLED\nis true.", AMBER),
        ("CycloneDX 1.7", "SBOM from the manifest.\nValidated against the\nlocal schema file.", BLUE),
    ]
    for index, (title, body, accent) in enumerate(stores):
        x = 0.42 + index * 3.22
        rect(s, x, 2.9, 3.05, 1.95, CARD, LINE)
        add_text(s, x + 0.16, 3.04, 2.75, 0.3, title, 15, accent, True)
        add_text(s, x + 0.16, 3.42, 2.75, 1.25, body, 13, MUTED, spacing=2)
    rect(s, 0.42, 5.05, 12.5, 1.8, CARD, LINE)
    add_text(s, 0.64, 5.2, 12.05, 0.26, "HASH REQUEST PATH", 12, CYAN, True)
    add_text(
        s,
        0.64,
        5.52,
        12.05,
        1.15,
        "Hash Checker  →  hashFile() or verifyFile() in api.ts  →  POST /api/integrity/hash or /verify\n→  read_upload_hashed()  →  hash_result()  →  envelope() writes the history row.\nThe file is hashed in 64 KiB chunks. The bytes are not stored and are not executed.",
        15,
        MUTED,
        spacing=3,
    )
    deck.footer(s, "Architecture")

    # 6 SHA-256
    s = deck.add(
        """On the Hash Checker page I upload a small file. Calculate SHA-256 streams the file through hashlib.sha256 and shows the digest. The verdict is NOT VERIFIED, because no reference was compared.
I paste that digest and choose Compare Hashes. The API normalizes the reference, including an optional sha256: prefix, and compares it with hmac.compare_digest. The screen says PASS. The stored verdict is MATCH.
I change one hexadecimal character and compare again. The screen says FAIL. The stored verdict is MISMATCH. That proves the bytes differ from the reference I typed. It does not say who changed the file, and it does not say the original file was safe."""
    )
    deck.kicker(s, "SHA-256 file integrity")
    deck.title(s, "Same bytes, or not the same bytes")
    steps = [
        ("1", "Upload", "The browser sends the file. The server hashes 64 KiB chunks."),
        ("2", "Digest", "hashlib.sha256 returns 64 hexadecimal characters."),
        ("3", "Compare", "hmac.compare_digest checks the supplied reference."),
    ]
    for index, (num, title, body) in enumerate(steps):
        x = 0.42 + index * 4.25
        rect(s, x, 1.28, 4.05, 1.55, CARD, LINE)
        add_text(s, x + 0.16, 1.4, 0.4, 0.32, num, 16, CYAN, True)
        add_text(s, x + 0.55, 1.4, 3.3, 0.32, title, 16, WHITE, True)
        add_text(s, x + 0.16, 1.85, 3.75, 0.75, body, 13, MUTED)
    outcomes = [
        ("NOT VERIFIED", "Digest only. No reference was compared.", DIM),
        ("PASS", "API verdict MATCH. The bytes equal the reference.", GREEN),
        ("FAIL", "API verdict MISMATCH. The bytes differ.", RED),
    ]
    for index, (title, body, accent) in enumerate(outcomes):
        x = 0.42 + index * 4.25
        rect(s, x, 3.05, 4.05, 1.7, CARD, LINE)
        add_text(s, x + 0.18, 3.2, 3.7, 0.36, title, 18, accent, True)
        add_text(s, x + 0.18, 3.68, 3.7, 0.85, body, 14, MUTED)
    rect(s, 0.42, 4.95, 12.5, 1.9, CARD_ALT, LINE)
    add_text(s, 0.64, 5.12, 12.1, 0.28, "WHAT A MATCH DOES NOT ESTABLISH", 12, AMBER, True)
    add_text(s, 0.64, 5.5, 12.05, 1.1, "It does not name the publisher. It does not prove the reference itself was honest. It does not prove the file is free of malware or vulnerabilities.\nAn empty file has the standard SHA-256 digest e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855. The test suite checks that value.", 14, MUTED, spacing=4)
    deck.footer(s, "SHA-256")

    # 7 HMAC
    s = deck.add(
        """HMAC is a shared-secret check. If I leave the secret blank, generate_secret uses secrets.token_hex(32), a 256-bit value shown as 64 hex characters. compute_tag uses HMAC-SHA256 over the UTF-8 message.
The tag and the secret come back to the browser so I can copy them. The history row does not contain them. The test reads the SQLite file and asserts that the secret and the tag are absent.
Verify recomputes the tag and uses compare_digest. PASS means VALID. If I change the message, the same secret and tag produce FAIL, stored as INVALID. The API does not say whether the message, the secret, or the tag was wrong.
This is not a digital signature. Both sides can create the tag, so I do not claim non-repudiation."""
    )
    deck.kicker(s, "HMAC-SHA256 authentication")
    deck.title(s, "A shared secret, not a public identity")
    rect(s, 0.42, 1.28, 4.0, 5.5, CARD, LINE)
    add_text(s, 0.64, 1.46, 3.6, 0.26, "MODEL", 12, CYAN, True)
    add_text(s, 0.64, 1.9, 3.55, 4.5, "Both parties already share a secret.\n\nTag = HMAC-SHA256\n(secret, message).\n\nCryptoGuard does not distribute the secret and does not write it to SQLite.\n\nA wrong message, secret, or tag is simply INVALID.", 15, MUTED, spacing=2)
    checks = [
        (GREEN, "PASS", "Same message, secret, and tag. Stored verdict: VALID."),
        (RED, "FAIL", "Change the message. Same secret and tag. Stored verdict: INVALID."),
        (AMBER, "LIMIT", "No public identity. No non-repudiation. The secret must stay secret."),
    ]
    for index, (accent, title, body) in enumerate(checks):
        y = 1.28 + index * 1.85
        rect(s, 4.65, y, 8.25, 1.7, CARD, LINE)
        add_text(s, 4.88, y + 0.22, 2.2, 0.4, title, 20, accent, True)
        add_text(s, 7.15, y + 0.28, 5.5, 1.15, body, 16, MUTED)
    deck.footer(s, "HMAC-SHA256")

    # 8 Signatures
    s = deck.add(
        """Key generation uses RSA with a 2048-bit modulus and public exponent 65537. The private key is unencrypted PKCS#8 PEM. The public key is SubjectPublicKeyInfo PEM. A pasted key smaller than 2048 bits is rejected.
Signing covers the exact UTF-8 message, with no added newline. The padding is RSA-PSS, MGF1 with SHA-256, and a salt length equal to the SHA-256 digest length, 32 bytes. The signature is base64.
Verification uses the public key. PASS means that key accepts the signature over those bytes. If I edit the message and keep the signature, verification returns FAIL.
The private key is returned once and is not stored. A valid result still does not name a person unless I already trust that public key."""
    )
    deck.kicker(s, "Digital signatures")
    deck.title(s, "RSA-2048 with RSA-PSS and SHA-256")
    params = [
        ("Key", "2048-bit RSA, public exponent 65537"),
        ("Private key", "Unencrypted PKCS#8 PEM, shown once, not stored"),
        ("Padding", "RSA-PSS, MGF1-SHA256, salt length 32 bytes"),
        ("Signed bytes", "Exact UTF-8 text of the message"),
        ("Signature", "Base64 on the wire and on screen"),
    ]
    for index, (label, value) in enumerate(params):
        y = 1.25 + index * 0.72
        rect(s, 0.42, y, 7.55, 0.64, CARD, LINE, radius=0.15)
        add_text(s, 0.6, y + 0.14, 1.9, 0.36, label, 14, CYAN, True)
        add_text(s, 2.55, y + 0.14, 5.2, 0.36, value, 14, WHITE)
    rect(s, 8.15, 1.25, 4.75, 2.35, CARD, LINE)
    add_text(s, 8.35, 1.42, 4.4, 0.26, "UNCHANGED RECORD", 12, GREEN, True)
    add_text(s, 8.35, 1.85, 4.35, 1.4, "The matching public key accepts the signature. The screen shows PASS.", 16, MUTED)
    rect(s, 8.15, 3.78, 4.75, 2.35, CARD, LINE)
    add_text(s, 8.35, 3.95, 4.4, 0.26, "MODIFIED RECORD", 12, RED, True)
    add_text(s, 8.35, 4.38, 4.35, 1.4, "One changed character makes the same signature FAIL. A different public key also fails.", 16, MUTED)
    add_text(s, 0.42, 6.35, 12.4, 0.55, "Trusting the public key is a separate requirement. CryptoGuard does not bind a key to a company or a person.", 15, AMBER)
    deck.footer(s, "RSA-PSS")

    # 9 Demonstration
    s = deck.add(
        """This slide is the demonstration map, not a screenshot. I will use the live application.
Hash Checker at /integrity: calculate, compare for PASS, change one hex character for FAIL.
HMAC Verifier at /hmac: generate a tag, verify PASS, change the message, verify FAIL, then clear the secret.
Digital Signatures at /signatures: generate a key pair, sign the release line, verify PASS, edit the line, verify FAIL.
If time remains, open Reports at /history and show the new rows, the CSV export, and one JSON report. I will not claim a result that the screen does not show."""
    )
    deck.kicker(s, "Practical demonstration")
    deck.title(s, "The live application, not a simulated result")
    demos = [
        ("01", "Hash Checker", "/integrity", "Calculate SHA-256, then Compare Hashes.", "PASS, then FAIL after one hex change."),
        ("02", "HMAC Verifier", "/hmac", "Generate authentication tag, then Verify tag.", "PASS, then FAIL after the message changes."),
        ("03", "Digital Signatures", "/signatures", "Generate key pair, Sign message, Verify signature.", "PASS, then FAIL after the text changes."),
        ("04", "Reports", "/history", "Open the new rows. Export CSV or download JSON.", "Sanitized history. No secret and no private key."),
    ]
    for index, (num, title, route, action, result) in enumerate(demos):
        y = 1.25 + index * 1.35
        rect(s, 0.42, y, 12.5, 1.22, CARD, LINE, radius=0.1)
        add_text(s, 0.6, y + 0.28, 0.7, 0.5, num, 18, CYAN, True)
        add_text(s, 1.4, y + 0.16, 3.3, 0.4, title, 16, WHITE, True)
        add_text(s, 1.4, y + 0.58, 3.3, 0.4, route, 13, CYAN)
        add_text(s, 4.9, y + 0.28, 4.3, 0.7, action, 14, MUTED)
        add_text(s, 9.3, y + 0.28, 3.4, 0.7, result, 14, WHITE)
    deck.footer(s, "Demonstration")

    # 10 Case study
    s = deck.add(
        """This case study is hypothetical. It is not a report of a real company or a real incident.
Harborline Instruments receives a vendor update with the expected filename. CryptoGuard can compare the file with the vendor’s published SHA-256 value. A mismatch is a reason to stop. A match shows byte equality with that reference only.
A signed release note can be checked with RSA-PSS if Harborline already holds the vendor’s public key through a trusted channel. HMAC fits a different workflow: two internal systems that already share a secret.
If verification fails, the company should not install the file. Obtaining the key, scanning for malware, and producing SLSA provenance require controls beyond this project."""
    )
    deck.kicker(s, "Case study  ·  hypothetical")
    deck.title(s, "Detect an altered download before acceptance")
    rows = [
        ["Altered file bytes", "SHA-256 comparison", "Bytes differ from the reference", "Does not name the attacker"],
        ["Edited release note", "RSA-PSS verification", "This public key rejects the signature", "The key must already be trusted"],
        ["Forged status message", "HMAC-SHA256", "The tag does not match the secret", "A stolen secret fools both sides"],
        ["Unknown vulnerabilities", "OSV exact-version query", "Advisories returned, or none found", "Empty is not proof of safety"],
    ]
    shape = s.shapes.add_table(5, 4, Inches(0.38), Inches(1.28), Inches(12.55), Inches(4.55))
    table = shape.table
    for index, width in enumerate([2.9, 3.15, 3.45, 3.05]):
        table.columns[index].width = Inches(width)
    for col, header in enumerate(["Threat", "CryptoGuard control", "What it can establish", "Remaining limit"]):
        write_cell(table.cell(0, col), header, 13, WHITE, True, fill=CARD_ALT)
    table.rows[0].height = Inches(0.5)
    for r, row in enumerate(rows, start=1):
        table.rows[r].height = Inches(0.95)
        for c, value in enumerate(row):
            write_cell(table.cell(r, c), value, 13, WHITE, c == 0, fill=CARD if r % 2 else RGBColor(0x12, 0x1C, 0x2E))
    add_text(s, 0.42, 6.05, 12.4, 0.85, "Harborline Instruments is a teaching scenario. A successful check is not a complete software security assessment. SLSA build provenance and malware analysis are outside CryptoGuard.", 14, MUTED)
    deck.footer(s, "Case study")

    # 11 Testing
    s = deck.add(
        """These results were produced on 19 October 2026. I am not quoting a percentage from another source.
From the backend virtual environment, pytest reported 25 passed and 1 skipped. The skipped test is the live OSV call. It runs only when CRYPTOGUARD_LIVE_API equals 1. That skip is not a cryptographic failure.
In the frontend, npm test ran Vitest: 6 files and 19 tests passed. Those tests check form validation, the PASS and FAIL labels, navigation, and mocked API errors.
The cryptographic tests cover a matching digest, a mismatch, a tampered HMAC message, a secret absent from SQLite, a changed signature message, a wrong public key, a 1024-bit key rejection, and CSV history."""
    )
    deck.kicker(s, "Testing and validation")
    deck.title(s, "Results from this workspace, 19 October 2026")
    rect(s, 0.42, 1.25, 4.0, 1.45, CARD, LINE)
    add_text(s, 0.62, 1.38, 3.6, 0.24, "BACKEND PYTEST", 12, CYAN, True)
    add_text(s, 0.62, 1.7, 3.6, 0.7, "25 passed    ·    1 skipped", 20, WHITE, True)
    rect(s, 4.6, 1.25, 4.0, 1.45, CARD, LINE)
    add_text(s, 4.8, 1.38, 3.6, 0.24, "FRONTEND VITEST", 12, CYAN, True)
    add_text(s, 4.8, 1.7, 3.6, 0.7, "19 passed    ·    6 files", 20, WHITE, True)
    rect(s, 8.78, 1.25, 4.12, 1.45, CARD, LINE)
    add_text(s, 8.98, 1.38, 3.75, 0.24, "LIVE OSV TEST", 12, AMBER, True)
    add_text(s, 8.98, 1.7, 3.75, 0.75, "Skipped unless\nCRYPTOGUARD_LIVE_API=1", 16, WHITE, True)
    scenarios = [
        ("SHA-256 match and mismatch", "MATCH and MISMATCH", "Passed"),
        ("HMAC tamper; secret not in SQLite", "VALID, then INVALID", "Passed"),
        ("RSA-PSS tamper, wrong key, 1024-bit key", "VALID, INVALID, HTTP 400", "Passed"),
        ("History detail, CSV export, delete", "Row, CSV, then 404", "Passed"),
        ("Frontend PASS / FAIL labels", "MATCH shown as PASS", "Passed"),
    ]
    shape = s.shapes.add_table(6, 3, Inches(0.42), Inches(2.9), Inches(12.48), Inches(3.55))
    table = shape.table
    for index, width in enumerate([5.5, 4.3, 2.68]):
        table.columns[index].width = Inches(width)
    for col, header in enumerate(["Scenario covered by the suite", "Expected outcome", "This run"]):
        write_cell(table.cell(0, col), header, 13, WHITE, True, fill=CARD_ALT)
    table.rows[0].height = Inches(0.42)
    for r, row in enumerate(scenarios, start=1):
        table.rows[r].height = Inches(0.58)
        for c, value in enumerate(row):
            color = GREEN if c == 2 else WHITE
            write_cell(table.cell(r, c), value, 13, color, c == 2, fill=CARD)
    deck.footer(s, "Testing")

    # 12 Security
    s = deck.add(
        """The threat model is local and honest about its boundary.
CryptoGuard can show byte inequality, an HMAC mismatch, and a signature rejection. Digest comparison uses hmac.compare_digest. Uploads stop at 10 MiB by default. Only the base file name is stored. Secrets and private keys are kept out of the history metadata.
The trust assumptions are outside the algorithms. The reference digest must come from a trustworthy place. The public key must already belong to the signer the user intends. The person operating the browser must protect the secret and the private key, because the server returns them and does not store them.
A malicious reference, a stolen HMAC secret, or a stolen private key defeats the corresponding check. The application also does not detect malware."""
    )
    deck.kicker(s, "Security analysis")
    deck.title(s, "What the checks cover, and what they assume")
    columns = [
        ("COVERED", GREEN, "Byte change against a reference\nHMAC tag mismatch\nRSA-PSS rejection\nSecrets kept out of SQLite\n10 MiB upload limit"),
        ("ASSUMED", CYAN, "The reference digest is honest\nThe public key is the right one\nThe local API is the one you started\nThe operator protects key material"),
        ("STILL OPEN", AMBER, "A malicious reference digest\nA leaked HMAC secret\nA leaked RSA private key\nNo malware detection\nNo user accounts"),
    ]
    for index, (title, accent, body) in enumerate(columns):
        x = 0.42 + index * 4.25
        rect(s, x, 1.3, 4.05, 4.35, CARD, LINE)
        add_text(s, x + 0.2, 1.48, 3.65, 0.32, title, 14, accent, True)
        add_text(s, x + 0.2, 2.0, 3.65, 3.35, body, 16, MUTED, spacing=8)
    add_text(s, 0.42, 6.05, 12.4, 0.85, "If the backend is down, the page reports that it cannot reach CryptoGuard. That error is not shown as a cryptographic FAIL.", 15, MUTED)
    deck.footer(s, "Security")

    # 13 Limitations
    s = deck.add(
        """I want to keep the boundary clear.
The application does hash files, verify HMAC tags, generate and check RSA-PSS signatures, verify a small provenance record, parse npm and Python manifests, query OSV, generate a CycloneDX 1.7 SBOM, and export history.
It does not create accounts, install packages, detect malware, or implement SLSA, in-toto, or Sigstore. NVD lookup exists and is disabled by default. PostgreSQL is a possible later database, not a tested deployment. There is no Alembic migration.
If I had another semester, I would bind public keys to named identities, encrypt private keys at rest, and add a repeatable live-OSV demonstration that is marked as a network check rather than a safety proof."""
    )
    deck.kicker(s, "Limitations and future scope")
    deck.title(s, "Implemented now, proposed later")
    rect(s, 0.42, 1.28, 6.2, 5.45, CARD, LINE)
    add_text(s, 0.64, 1.46, 5.8, 0.3, "IN THIS PROJECT", 13, GREEN, True)
    add_text(
        s,
        0.64,
        1.95,
        5.75,
        4.4,
        "SHA-256 hash and reference comparison\nHMAC-SHA256 generate and verify\nRSA-2048 key pair, sign, and verify\nCanonical provenance record\nOSV query and CycloneDX 1.7 SBOM\nSQLite history, CSV, and JSON report",
        16,
        WHITE,
        spacing=8,
    )
    rect(s, 6.82, 1.28, 6.08, 5.45, CARD, LINE)
    add_text(s, 7.04, 1.46, 5.65, 0.3, "NOT IN THIS PROJECT", 13, AMBER, True)
    add_text(
        s,
        7.04,
        1.95,
        5.6,
        4.4,
        "User accounts and key custody\nMalware or package-name reputation\nFull SLSA, in-toto, or Sigstore\nPackage installation or script execution\nNVD enabled by default\nA tested PostgreSQL deployment",
        16,
        WHITE,
        spacing=8,
    )
    deck.footer(s, "Limitations")

    # 14 Conclusion
    s = deck.add(
        """To close: CryptoGuard is a teaching platform that runs three different cryptographic checks and refuses to blur them.
SHA-256 answers whether the bytes match a reference. HMAC-SHA256 answers whether the shared secret authenticates the message. RSA-PSS answers whether the supplied public key accepts the signature. Supply-chain pages add OSV evidence and an SBOM, with their own limits.
The tests I reported passed, with the live OSV test skipped. The important limit remains: a successful check is evidence about the inputs I supplied. It is not a complete statement that the software is safe."""
    )
    deck.kicker(s, "Conclusion")
    deck.title(s, "Evidence, labeled honestly")
    points = [
        ("Integrity", "A SHA-256 match means the file bytes equal the reference that was supplied."),
        ("Authentication", "An HMAC-SHA256 tag authenticates a message only for holders of the shared secret."),
        ("Signature", "RSA-PSS shows that this public key accepts this signature over these bytes."),
        ("Boundary", "None of the three results is a malware verdict or a full supply-chain attestation."),
    ]
    for index, (title, body) in enumerate(points):
        y = 1.28 + index * 1.2
        rect(s, 0.42, y, 12.5, 1.08, CARD, LINE, radius=0.12)
        add_text(s, 0.66, y + 0.16, 2.4, 0.7, title, 16, CYAN, True, anchor=MSO_ANCHOR.MIDDLE)
        add_text(s, 3.2, y + 0.22, 9.4, 0.68, body, 16, WHITE, anchor=MSO_ANCHOR.MIDDLE)
    deck.footer(s, "Conclusion")

    # 15 Thank you
    s = deck.add(
        """Thank you. I am happy to take questions.
If you would like to see the running system, the site is on port 5173, the health check is /api/health on port 8000, and the interactive API documentation is /docs.
I will answer from the implementation: SHA-256, HMAC-SHA256, and RSA-PSS, and I will say when a control is outside the project."""
    )
    add_text(s, 0.55, 1.7, 12, 0.4, "CRYPTOGUARD", 14, CYAN, True)
    add_text(s, 0.55, 2.2, 12, 1.1, "Thank you.", 60, WHITE, True)
    add_text(s, 0.55, 3.5, 12, 0.7, "Questions?", 36, BLUE, True)
    add_text(s, 0.55, 4.6, 11.5, 1.3, "Health    http://127.0.0.1:8000/api/health\nAPI docs    http://127.0.0.1:8000/docs\nApplication    http://127.0.0.1:5173", 16, MUTED, spacing=4)
    deck.footer(s, "Close")
    return deck


def validate(path: str) -> None:
    prs = Presentation(path)
    errors = []
    if len(prs.slides) != 15:
        errors.append(f"expected 15 slides, found {len(prs.slides)}")
    width = prs.slide_width
    height = prs.slide_height
    for index, slide in enumerate(prs.slides, start=1):
        texts = []
        for shape in slide.shapes:
            if shape.left < -Emu(20000) or shape.top < -Emu(20000):
                errors.append(f"slide {index} shape starts off-canvas")
            if shape.left + shape.width > width + Emu(20000):
                errors.append(f"slide {index} shape extends past the right edge")
            if shape.top + shape.height > height + Emu(20000):
                errors.append(f"slide {index} shape extends past the bottom edge")
            if shape.has_text_frame:
                value = "\n".join(paragraph.text for paragraph in shape.text_frame.paragraphs).strip()
                if value:
                    texts.append(value)
        if not texts:
            errors.append(f"slide {index} has no text")
        notes = slide.notes_slide.notes_text_frame.text.strip()
        if len(notes) < 80:
            errors.append(f"slide {index} speaker notes are too short")
    if errors:
        raise SystemExit("Presentation validation failed:\n- " + "\n- ".join(errors))
    print(f"Validated {len(prs.slides)} slides in {path}")


if __name__ == "__main__":
    from pathlib import Path

    output = Path(__file__).resolve().parents[1] / "CryptoGuard_HOD_Presentation.pptx"
    presentation = build()
    presentation.save(str(output))
    validate(str(output))
