import asyncio
from collections.abc import Iterator
from typing import NoReturn

import httpx
import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import StaticPool

from api.app.db import get_engine
from api.app.main import app


class _UnreachableEngine:
    """Stands in for the database boundary being down: every connect attempt fails."""

    def connect(self) -> NoReturn:
        raise OperationalError("SELECT 1", None, OSError("connection refused"))


def _get(path: str) -> httpx.Response:
    """Drive the ASGI app over httpx without Starlette's deprecated TestClient."""

    async def _call() -> httpx.Response:
        transport: httpx.ASGITransport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://wtw.test"
        ) as client:
            return await client.get(path)

    return asyncio.run(_call())


@pytest.fixture(autouse=True)
def _clear_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def reachable_engine() -> Iterator[Engine]:
    """A real, single-connection SQLite engine, disposed deterministically after use."""
    engine: Engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    yield engine
    engine.dispose()


def test_health_is_ok_when_database_is_reachable(reachable_engine: Engine) -> None:
    app.dependency_overrides[get_engine] = lambda: reachable_engine

    response: httpx.Response = _get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


def test_health_is_degraded_when_database_is_unreachable() -> None:
    app.dependency_overrides[get_engine] = _UnreachableEngine

    response: httpx.Response = _get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "down"}
