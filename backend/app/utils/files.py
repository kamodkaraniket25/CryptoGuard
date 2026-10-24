"""Safe upload reading. File bytes are hashed in chunks and never executed."""

import hashlib
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings


class PayloadTooLarge(Exception):
    def __init__(self, limit: int):
        self.limit = limit
        super().__init__(f"Upload exceeds the maximum size of {limit} bytes.")


def safe_filename(name: str | None) -> str:
    raw = name or "upload"
    base = Path(raw.replace("\\", "/")).name
    cleaned = "".join(ch for ch in base if ch.isprintable() and ch not in "\r\n\t")
    cleaned = cleaned.strip().strip(".")
    if not cleaned or cleaned in {".", ".."}:
        return "upload"
    return cleaned[:255]


async def read_upload_hashed(upload: UploadFile) -> tuple[str, int, str]:
    settings = get_settings()
    filename = safe_filename(upload.filename)
    hasher = hashlib.sha256()
    size = 0
    while True:
        chunk = await upload.read(settings.chunk_size)
        if not chunk:
            break
        size += len(chunk)
        if size > settings.max_upload_bytes:
            raise PayloadTooLarge(settings.max_upload_bytes)
        hasher.update(chunk)
    await upload.close()
    return filename, size, hasher.hexdigest()


async def read_upload_text(upload: UploadFile) -> tuple[str, str]:
    settings = get_settings()
    filename = safe_filename(upload.filename)
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = await upload.read(settings.chunk_size)
        if not chunk:
            break
        size += len(chunk)
        if size > settings.max_upload_bytes:
            raise PayloadTooLarge(settings.max_upload_bytes)
        chunks.append(chunk)
    await upload.close()
    try:
        text = b"".join(chunks).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("The uploaded file must be UTF-8 text.") from exc
    return filename, text
