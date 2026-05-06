"""Pytest fixtures for the financial analytics dashboard test suite.

Test DB strategy:
- A dedicated `<DB_NAME>_test` database is created at session start, schema
  applied via migrations/init.sql, dropped at session end.
- Each test gets a session wrapped in an outer transaction. The session
  uses `join_transaction_mode="create_savepoint"` so service-layer
  commits become savepoints inside the outer transaction. Teardown
  rolls back the outer transaction, undoing every change the test made
  — even committed ones.

Seed dataset (function-scoped via `seeded_db`):
- 1 user, 4 categories, 10 transactions across 2026 + 2025, 3 budgets.
- Numbers are deterministic; tests can assert exact values.

The `async_client` fixture is used by smoke tests; integration tests in
commit #11 will add an `authenticated_client` variant that overrides the
app's `get_session` dependency to use the test DB.
"""

from datetime import date
from pathlib import Path
from typing import AsyncIterator

import asyncpg
import bcrypt
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.database.connection import get_session
from app.main import app


TEST_DB_NAME = f"{settings.db_name}_test"
INIT_SQL_PATH = Path(__file__).resolve().parent.parent / "migrations" / "init.sql"


def _admin_dsn() -> str:
    return (
        f"postgresql://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/postgres"
    )


def _test_db_dsn() -> str:
    return (
        f"postgresql://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{TEST_DB_NAME}"
    )


def _test_db_async_url() -> str:
    return (
        f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{TEST_DB_NAME}"
    )


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def test_db():
    admin_conn = await asyncpg.connect(dsn=_admin_dsn())
    try:
        await admin_conn.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"')
        await admin_conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await admin_conn.close()

    test_conn = await asyncpg.connect(dsn=_test_db_dsn())
    try:
        sql = INIT_SQL_PATH.read_text()
        await test_conn.execute(sql)
    finally:
        await test_conn.close()

    yield TEST_DB_NAME

    admin_conn = await asyncpg.connect(dsn=_admin_dsn())
    try:
        await admin_conn.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"')
    finally:
        await admin_conn.close()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def test_engine(test_db):
    engine = create_async_engine(_test_db_async_url(), echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncIterator[AsyncSession]:
    """Per-test session inside an outer transaction. Service-layer commits
    land as savepoints; the outer rollback at teardown wipes the lot."""
    async with test_engine.connect() as conn:
        trans = await conn.begin()
        session_factory = async_sessionmaker(
            bind=conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        async with session_factory() as session:
            yield session
        await trans.rollback()


@pytest_asyncio.fixture
async def seeded_db(test_session: AsyncSession) -> int:
    """Insert a deterministic dataset and return the new user_id.

    Layout:
      User: 1 row (username=demo)
      Categories: 4 (Salary income, Food/Rent/Transport expense)
      Transactions in June 2026:
        - Salary    $4,000.00 (06-01) "June salary"
        - Food        $100.00 (06-05) "Groceries"
        - Food         $75.00 (06-12) "Restaurant"
        - Rent      $1,200.00 (06-01) "Rent"
        - Transport    $50.00 (06-10) "Gas"
      Transactions in May 2026:
        - Salary    $4,000.00 (05-01) "May salary"
        - Food        $250.00 (05-05) "May groceries"
        - Rent      $1,200.00 (05-01) "May rent"
      Transactions in 2025 (for year-filter tests):
        - Salary    $4,000.00 (2025-06-01) "2025 salary"
        - Food         $50.00 (2025-06-15) "2025 food"
      Budgets in June 2026: Food $200, Rent $1,200, Transport $30
    """
    pwd = bcrypt.hashpw(b"testpass", bcrypt.gensalt()).decode("utf-8")

    user_result = await test_session.execute(
        text(
            "INSERT INTO users (username, display_name, password_hash) "
            "VALUES (:u, :d, :p) RETURNING id"
        ),
        {"u": "demo", "d": "Demo User", "p": pwd},
    )
    user_id = user_result.scalar_one()

    cats: dict[str, int] = {}
    category_specs = [
        ("Salary", "income", "#2E8B57"),
        ("Food", "expense", "#FF6384"),
        ("Rent", "expense", "#FFCE56"),
        ("Transport", "expense", "#36A2EB"),
    ]
    for name, type_, color in category_specs:
        result = await test_session.execute(
            text(
                "INSERT INTO categories (name, type, color) "
                "VALUES (:n, :t, :c) RETURNING id"
            ),
            {"n": name, "t": type_, "c": color},
        )
        cats[name] = result.scalar_one()

    transactions = [
        (cats["Salary"],    "4000.00", date(2026, 6, 1),  "June salary"),
        (cats["Food"],       "100.00", date(2026, 6, 5),  "Groceries"),
        (cats["Food"],        "75.00", date(2026, 6, 12), "Restaurant"),
        (cats["Rent"],      "1200.00", date(2026, 6, 1),  "Rent"),
        (cats["Transport"],   "50.00", date(2026, 6, 10), "Gas"),
        (cats["Salary"],    "4000.00", date(2026, 5, 1),  "May salary"),
        (cats["Food"],       "250.00", date(2026, 5, 5),  "May groceries"),
        (cats["Rent"],      "1200.00", date(2026, 5, 1),  "May rent"),
        (cats["Salary"],    "4000.00", date(2025, 6, 1),  "2025 salary"),
        (cats["Food"],        "50.00", date(2025, 6, 15), "2025 food"),
    ]
    for cat_id, amount, tx_date, desc in transactions:
        await test_session.execute(
            text(
                "INSERT INTO transactions "
                "(user_id, category_id, amount, date, description) "
                "VALUES (:user_id, :cat_id, :amount, :date, :desc)"
            ),
            {
                "user_id": user_id,
                "cat_id": cat_id,
                "amount": amount,
                "date": tx_date,
                "desc": desc,
            },
        )

    budgets = [
        (cats["Food"],       "200.00"),
        (cats["Rent"],      "1200.00"),
        (cats["Transport"],   "30.00"),
    ]
    for cat_id, amount in budgets:
        await test_session.execute(
            text(
                "INSERT INTO budgets (user_id, category_id, amount, month, year) "
                "VALUES (:user_id, :cat_id, :amount, 6, 2026)"
            ),
            {"user_id": user_id, "cat_id": cat_id, "amount": amount},
        )

    await test_session.commit()  # Becomes a savepoint inside outer txn
    return user_id


@pytest_asyncio.fixture
async def async_client() -> AsyncIterator[AsyncClient]:
    """Foundation HTTP client (no DB override). Used by smoke tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ---------- Integration-test fixtures (truncate-based isolation) ----------
# Service-layer tests use test_session+seeded_db with savepoint rollback.
# Integration tests can't use that pattern because the FastAPI app opens
# its own session per request — different from the test's session — so
# savepoint changes wouldn't be visible to the request handler. Instead
# we TRUNCATE all tables before each integration test, override the app's
# get_session to use the test engine, and let request handlers commit
# normally. The next test's TRUNCATE wipes the slate.

@pytest_asyncio.fixture
async def app_with_test_db(test_engine):
    """Truncate all tables, override the app's get_session to use the test
    engine. Yields a SessionLocal so tests can seed/inspect.

    Truncates on BOTH setup and teardown so service-layer tests (which use
    test_session/seeded_db with savepoint rollback) see a clean DB after
    any integration test that committed data.
    """
    SessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)
    truncate_sql = text(
        "TRUNCATE users, transactions, budgets, categories "
        "RESTART IDENTITY CASCADE"
    )

    async with SessionLocal() as session:
        await session.execute(truncate_sql)
        await session.commit()

    async def override_get_session():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    yield SessionLocal
    app.dependency_overrides.clear()

    async with SessionLocal() as session:
        await session.execute(truncate_sql)
        await session.commit()


@pytest_asyncio.fixture
async def unauthed_client(app_with_test_db) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def demo_user_in_db(app_with_test_db):
    """Insert a demo user with password 'testpass' and return SessionLocal."""
    SessionLocal = app_with_test_db
    pwd = bcrypt.hashpw(b"testpass", bcrypt.gensalt()).decode("utf-8")
    async with SessionLocal() as session:
        await session.execute(
            text(
                "INSERT INTO users (username, display_name, password_hash) "
                "VALUES (:u, :d, :p)"
            ),
            {"u": "demo", "d": "Demo User", "p": pwd},
        )
        await session.commit()
    return SessionLocal


@pytest_asyncio.fixture
async def authed_client(demo_user_in_db) -> AsyncIterator[AsyncClient]:
    """HTTP client with a valid session cookie for demo / testpass."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/login",
            data={"username": "demo", "password": "testpass"},
            follow_redirects=False,
        )
        assert response.status_code == 302, "fixture login failed"
        yield client
