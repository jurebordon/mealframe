"""Shared httpx transport for nutrition clients.

Tests override ``_transport`` with an ``httpx.MockTransport`` to stub upstream calls.
Production code leaves it as ``None`` and gets the default httpx transport.
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx

_transport: httpx.AsyncBaseTransport | None = None


def set_transport(transport: httpx.AsyncBaseTransport | None) -> None:
    """Override the httpx transport (tests only)."""
    global _transport
    _transport = transport


@asynccontextmanager
async def async_client(**kwargs) -> AsyncIterator[httpx.AsyncClient]:
    """Yield an httpx.AsyncClient honoring the injected transport, if any."""
    if _transport is not None:
        async with httpx.AsyncClient(transport=_transport, **kwargs) as client:
            yield client
    else:
        async with httpx.AsyncClient(**kwargs) as client:
            yield client
