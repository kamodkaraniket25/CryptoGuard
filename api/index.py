"""Vercel Python entrypoint. The FastAPI app keeps its /api routes."""

import sys
from pathlib import Path


def _add_backend() -> None:
    here = Path(__file__).resolve()
    candidates = [Path.cwd() / "backend", here.parents[1] / "backend"]
    for candidate in candidates:
        if (candidate / "app" / "main.py").is_file():
            path = str(candidate)
            if path not in sys.path:
                sys.path.insert(0, path)
            return
    raise RuntimeError("CryptoGuard backend package was not found.")


_add_backend()

from app.main import app  # noqa: E402

__all__ = ["app"]
