# System Context — Financial Analytics Dashboard

> Dense reference for AI assistants and future maintainers picking up this project. Optimized for fast onboarding, not for narrative reading.

## TL;DR

Server-rendered FastAPI dashboard. PostgreSQL + asyncpg. SQL-first aggregation in services. Jinja2 templates with Chart.js charts. Session auth with bcrypt. CSV export via streaming. Layer-based architecture. 36 pytest tests passing.

## Stack

| Concern | Choice |
|---|---|
| Web | FastAPI ≥ 0.115, Uvicorn ≥ 0.30 |
| DB | PostgreSQL 16 + asyncpg, SQLAlchemy 2.0 async |
| Templating | Jinja2 (`templates.TemplateResponse(request, name, context)` — Starlette 0.40+ signature) |
| Charts | Chart.js 4.4 via CDN |
| Auth | Starlette `SessionMiddleware`, bcrypt direct (no passlib) |
| Tests | pytest + pytest-asyncio (`asyncio_mode=auto`, session-scoped loop) + httpx `ASGITransport` |
| Container | Multi-stage Dockerfile (builder + runtime), docker-compose `db → seed → app` |

## Layer-based architecture

```
Request → Router (auth check, query parsing)
        → Service (SQL aggregation, returns dataclass)
        → Template (Jinja2 rendering)
        → Response
```

No ORM objects cross layer boundaries. Service functions return plain dataclasses from `app/schemas/contracts.py`. Templates only see those dataclasses, so they're independent of DB internals.

## Key directories and what's in them

| Path | What |
|---|---|
| `app/main.py` | FastAPI app construction, middleware, router wiring, `/` and `/health` |
| `app/config.py` | pydantic-settings (DB creds, secret key, app debug flag) |
| `app/auth.py` | `/login`, `/logout`, `verify_password` (bcrypt), `require_login` dep |
| `app/database/connection.py` | Async engine, `SessionLocal`, `get_session` FastAPI dep |
| `app/routers/*.py` | One router per page; thin (parse query/form → service → template) |
| `app/services/*.py` | SQL aggregation per page; the project's most interesting code |
| `app/schemas/contracts.py` | Page-level dataclasses (`OverviewKPIs`, `BudgetRow`, etc.) |
| `app/schemas/entities.py` | DB-row dataclasses (`User`, `Transaction`, `Category`, `Budget`) |
| `app/templates/` | Jinja2 — `base.html` includes sidebar, defines `{% block %}`s |
| `app/static/style.css` | Single stylesheet, CSS variables, dark sidebar / light content |
| `migrations/init.sql` | Schema, indexes, constraints (mounted into Postgres on first start) |
| `seed/seed.py` | 12-month narrative seed; idempotent (skips if demo user exists) |
| `tests/conftest.py` | Two isolation strategies: savepoint (service tests), truncate (integration) |
| `docs/PROJECT_PLAN.md` | Implementation plan + commit checklist |
| `docs/TESTS.md` | Test inventory (manual + pytest, by phase) |

## Database schema

```sql
users        (id, username UNIQUE, password_hash, display_name, created_at)
categories   (id, name UNIQUE, type IN ('income','expense'), color HEX)
transactions (id, user_id FK, category_id FK, amount DECIMAL(10,2),
              date DATE, description, created_at, updated_at)
budgets      (id, user_id FK, category_id FK, amount, month, year,
              UNIQUE(user_id, category_id, month, year))

Indexes: idx_transactions_user_date, idx_transactions_category
```

Type lives on `Category`, not `Transaction` — keeps transactions lean and lets a single category change retag all its history.

## Service-layer entry points

| Service | Function | Returns |
|---|---|---|
| `overview_service` | `get_overview_data(session, user_id, month, year)` | `OverviewPageData` |
| `expenses_service` | `get_expenses_data(session, user_id, year)` | `ExpensesPageData` |
| `income_service` | `get_income_data(session, user_id, year)` | `IncomePageData` |
| `budget_service` | `get_budget_data(session, user_id, month, year)` | `BudgetPageData` |
| `transactions_service` | `list_transactions(...)`, `list_categories(session)`, `create_transaction(...)` | `TransactionListResult`, `list[CategoryOption]`, `int` |
| `export_service` | `transactions_to_csv(session, user_id)` | `AsyncIterator[str]` (streaming) |

## SQL patterns worth knowing

- **Window function for percent-of-total**: `ROUND(SUM(t.amount) * 100.0 / SUM(SUM(t.amount)) OVER (), 2)` — single-pass grand-total + per-row percentage.
- **NULL-safe filters in `list_transactions`**: `(CAST(:param AS TYPE) IS NULL OR col = :param)` — one query handles every combo of optional filters.
- **`COUNT(*) OVER ()` alongside `LIMIT/OFFSET`** — total matching count + the paged slice in one round trip.
- **`EXTRACT(MONTH FROM t.date)::int`** — explicit cast keeps it as Python int (default is Decimal).

## Auth flow

1. `POST /login` → `verify_password(plain, stored_hash)` using `bcrypt.checkpw`
2. On success: `request.session["user_id"] = row.id` → `RedirectResponse("/", 302)`
3. Protected routes use `Depends(require_login)`; missing session → 302 to `/login`
4. `GET /logout` → `request.session.clear()` → 302 to `/login`

Session cookie is signed with `itsdangerous` (Starlette dependency, must be in pyproject.toml — easy miss).

## Test infrastructure

Two isolation strategies in `tests/conftest.py`:

| Fixture | Strategy | When to use |
|---|---|---|
| `test_session` + `seeded_db` | Outer transaction + savepoint commits | Service-layer tests (no HTTP) |
| `app_with_test_db` + `authed_client` | TRUNCATE setup + teardown | Integration tests (HTTP) |

Why two? HTTP requests open their own sessions different from the test's session, so savepoint-mode commits aren't visible to the request handler. The truncate-pattern fixture cleans on BOTH setup and teardown so service tests run cleanly after integration tests.

The `seeded_db` fixture inserts a deterministic dataset (1 user, 4 categories, 10 transactions across 2026 + 2025, 3 budgets) — tests can assert exact values like `data.kpis.total_balance == 2575`.

## Known dependency gotchas

- **`itsdangerous`** — required by `SessionMiddleware`, must be explicit in pyproject.toml (FastAPI doesn't auto-pull it).
- **`python-multipart`** — required by `Form(...)`. Same situation.
- **`bcrypt` direct, not via passlib** — passlib 1.7.4 reads `bcrypt.__about__.__version__` which bcrypt 4.1+ removed. Use `bcrypt.hashpw` / `bcrypt.checkpw` directly.
- **`TemplateResponse(request, name, context)`** — new Starlette 0.40+ signature. Old `TemplateResponse(name, context)` raises a confusing `TypeError: unhashable type: 'dict'` because Starlette treats args[1] as the template name.
- **Jinja2 `{% block %}` inside `{% include %}` doesn't participate in extending template's block hierarchy.** Inline the markup in `base.html` instead.

## Conventions

- **Commits**: Conventional Commits (`type(scope): description`), `Co-Authored-By` trailer for AI-assisted work.
- **Branch**: `main` only; no feature branches in this solo project.
- **Style**: async + asyncpg + raw SQL via `text()`. Dataclass contracts. No ORM models.
- **Comments**: sparse; only WHY-comments where intent isn't obvious. No tutorial scaffolds.
- **Errors**: validate at boundaries (form input, query params); trust internal calls.

## Reference paths for further reading

- `docs/PROJECT_PLAN.md` — phase-by-phase implementation plan with commit hashes
- `docs/TESTS.md` — full test inventory and lessons captured
- README.md (top level) — portfolio-facing overview

## Quick verification commands

```bash
docker compose up -d                                     # start stack
docker compose exec app pytest tests/ -v                 # run tests (expect 36 passed)
docker compose exec db psql -U finance_user -d finance   # poke at the DB
curl -i http://localhost:3200/health                     # smoke test
```
