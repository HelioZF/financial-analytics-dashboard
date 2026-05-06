"""Pytest fixtures for the financial analytics dashboard test suite.

Foundation (commit #9):
- async_client: httpx.AsyncClient hitting the FastAPI app in-process via
  ASGITransport. No real HTTP socket; request lifecycle runs through the
  ASGI app directly.

DB- and seed-aware fixtures (test_db, test_session, seeded_db,
authenticated_client) come in commit #10 when service tests need them.
"""

from typing import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def async_client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
