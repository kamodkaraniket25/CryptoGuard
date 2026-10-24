"""CryptoGuard FastAPI application."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

import logging

from fastapi import HTTPException

from app.api.routes import router
from app.core.config import FULL_TITLE, PRODUCT_NAME, get_settings
from app.database import configure_database, init_db
from app.utils.files import PayloadTooLarge

logger = logging.getLogger("cryptoguard")


def _validation_errors(exc: RequestValidationError) -> list[dict]:
    cleaned = []
    for error in exc.errors():
        cleaned.append(
            {
                "loc": [str(part) for part in error.get("loc", [])],
                "msg": error.get("msg", "Invalid value"),
                "type": error.get("type", "value_error"),
            }
        )
    return cleaned


def create_app() -> FastAPI:
    settings = get_settings()
    configure_database(settings.database_url)
    init_db()
    app = FastAPI(
        title=PRODUCT_NAME,
        description=FULL_TITLE
        + " Academic MVP for file integrity, HMAC, digital signatures, provenance, SBOMs, and live vulnerability lookups.",
        version=settings.app_version,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def limit_json_body(request: Request, call_next):
        content_type = request.headers.get("content-type", "")
        length = request.headers.get("content-length")
        if content_type.startswith("application/json") and length:
            try:
                size = int(length)
            except ValueError:
                size = 0
            if size > settings.json_body_limit_bytes:
                return JSONResponse(status_code=413, content={"detail": "JSON body is too large."})
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": "The request was invalid.", "errors": _validation_errors(exc)})

    @app.exception_handler(PayloadTooLarge)
    async def too_large_handler(_request: Request, exc: PayloadTooLarge):
        return JSONResponse(status_code=413, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def unexpected_handler(_request: Request, exc: Exception):
        if isinstance(exc, HTTPException):
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        logger.exception("Unhandled CryptoGuard error")
        return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})

    @app.get("/", tags=["platform"])
    def root() -> dict:
        return {"product": PRODUCT_NAME, "full_title": FULL_TITLE, "health": "/api/health", "docs": "/docs"}

    app.include_router(router, prefix="/api")
    _attach_frontend(app)
    return app


def _frontend_dist() -> Path | None:
    """Built site used when a request is not an API route."""
    here = Path(__file__).resolve()
    repo = here.parents[2]
    candidates = [
        repo / "frontend" / "dist",
        repo / "public",
        Path.cwd() / "public",
        Path.cwd() / "frontend" / "dist",
    ]
    for candidate in candidates:
        if (candidate / "index.html").is_file():
            return candidate
    return None


def _attach_frontend(application: FastAPI) -> None:
    """Serve the built site for browser routes. API routes stay on the backend."""
    dist = _frontend_dist()
    if dist is None:
        return
    index = dist / "index.html"
    root = dist.resolve()

    @application.get("/{full_path:path}", include_in_schema=False)
    def frontend_page(full_path: str) -> FileResponse:
        if full_path == "api" or full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found."})
        candidate = (dist / full_path).resolve() if full_path else index
        try:
            candidate.relative_to(root)
        except ValueError:
            return FileResponse(index)
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)


app = create_app()
