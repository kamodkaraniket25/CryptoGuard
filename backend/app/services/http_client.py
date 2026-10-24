"""Shared async HTTP client. Tests can inject an httpx transport."""

from contextlib import asynccontextmanager

import httpx

_transport: httpx.BaseTransport | None = None


def set_transport(transport: httpx.BaseTransport | None) -> None:
    global _transport
    _transport = transport


@asynccontextmanager
async def http_client(timeout: float):
    headers = {
        "User-Agent": "CryptoGuard/1.0.0 (academic supply-chain verification)",
        "Accept": "application/json",
    }
    kwargs: dict = {"timeout": timeout, "headers": headers}
    if _transport is not None:
        kwargs["transport"] = _transport
    async with httpx.AsyncClient(**kwargs) as client:
        yield client
