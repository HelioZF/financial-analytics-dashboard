# Claude Context — Financial Analytics Dashboard

> **Read this file at the start of every conversation about this project.**
> It keeps context, progress, and rules synced across devices and conversations.

---

## Agent Rules

### Role: Advisor, NOT Programmer
- Helio is coding this project **by hand** to rebuild his programming skills after a layoff.
- **DO NOT** write full implementations, complete files, or modules.
- **DO** explain concepts, point to patterns, suggest approaches, and let Helio write the code.
- Small code snippets to illustrate a concept are OK, but never full files.
- When Helio asks "how should I do X?" — give the idea, let him figure out the implementation.
- Challenge questionable decisions — he wants to learn, not just ship.
- Review his code when asked, suggest improvements, help debug.

### English Training
- **Always** include an `## English Review` section at the end of every response.
- Analyze Helio's input for grammar, spelling, word choice, and phrasing.
- Show what was wrong and how to improve, in a table format.
- Helio is a Brazilian Portuguese native speaker — watch for common Portuguese false cognates and patterns:
  - "resume" vs "summary" (resumo)
  - "de" slipping in for "the"
  - "had" vs "have" (present perfect vs past perfect)
  - Third person singular -s ("it makes" not "it make")
  - Consonant + y plurals (category → categories, not categoryes)

### Critical Rules
- **NEVER** reference "Lux", "Bitrix", "Lux Energia", "CCEE", or any company name.
- **NEVER** include real financial data or employee names.
- No SQL Server / pyodbc — fully replaced with PostgreSQL + asyncpg.
- Seed data must tell a **financial story** (realistic monthly patterns, not random noise).
- PDF export is a **stretch goal** — CSV is the core deliverable.

---

## Project Overview

**Project 5 of 6** in Helio's portfolio — A personal finance dashboard built with server-side rendering (no React/SPA).

**GitHub:** https://github.com/HelioZF/financial-analytics-dashboard

**What it does:** Users visualize expenses, track income, compare budgets, and export financial data through a multi-page web dashboard with interactive charts.

---

## Tech Stack

| Component | Technology |
|---|---|
| Web Framework | FastAPI >=0.115 |
| ASGI Server | Uvicorn >=0.30 |
| Templating | Jinja2 (server-side rendering) |
| Database | PostgreSQL (Docker) + asyncpg (async driver) |
| ORM/Toolkit | SQLAlchemy >=2.0 |
| Data Processing | pandas >=2.2 |
| Charts | Chart.js (CDN, frontend) |
| Auth | Starlette SessionMiddleware + seeded demo user |
| Settings | pydantic-settings >=2.3 |
| Password Hashing | passlib[bcrypt] >=1.7 |
| Export | CSV (core) + PDF via reportlab (stretch) |
| Testing | pytest + httpx |
| Containerization | Docker + docker-compose |
| Python | >=3.10 |

---

## Architecture Decisions Made

These decisions were discussed and agreed upon. Don't revisit unless Helio asks:

1. **Async over sync** — Using asyncpg (not psycopg2) to show range in portfolio and align with modern FastAPI patterns.
2. **Category is its own table** — Normalized design. Transaction references category_id. Type (income/expense) lives on Category, not Transaction, to keep transactions lean.
3. **Balance is calculated, never stored** — Balance = SUM(income) - SUM(expenses). Derived at query time.
4. **Budget is one-per-category-per-month** — No many-to-many. Simple join for budget vs actual comparison.
5. **Layer-based architecture** (not Clean Architecture) — `database/`, `services/`, `routers/` folders. Simple and proportional to project size.
6. **Templates inside app/** — Not a separate frontend. SSR means templates are part of the backend's output.
7. **Session auth, not JWT** — SSR-appropriate pattern. JWT is showcased in Project 2.
8. **Seed data as separate Docker service** — Using Docker profiles for one-shot seeding.
9. **`migrations/` for SQL schema files** — Not `db/`.

---

## Entities (Defined)

```
User: id, display_name, username, password_hash
Transaction: id, user_id, amount, category_id, date, description
Category: id, name, type (str: "income"/"expense"), color
Budget: id, user_id, month (int), year (int), category_id, amount
```

**Pending fixes on entities.py:**
- `user_name` should be `username` (one word)
- Budget is missing `user_id`

---

## Contracts (In Progress)

### Overview Page — DONE
```
OverviewKPIs: month_reference, year_reference, total_income, total_expenses, total_balance
MonthlyTotal: month_reference, year_reference, amount, type
CategoryBreakdown: name, color, type, total_amount, percentage
OverviewPageData: kpis, monthly_data (List), income_breakdown (List), expense_breakdown (List)
```

### Remaining Pages — NOT STARTED
- Expenses page (category breakdown, monthly trends, top individual items)
- Income page (source breakdown, monthly trends)
- Budget page (budget vs actual per category, status indicators)
- Transactions page (filterable list, add transaction form)

Note: `CategoryBreakdown` and `MonthlyTotal` are reusable across pages.

---

## Project Structure

```
project5_analytics-dashboard-fastapi/
├── app/
│   ├── __init__.py
│   ├── main.py              (empty)
│   ├── config.py            (empty)
│   ├── auth.py              (empty)
│   ├── database/
│   │   └── __init__.py
│   ├── routers/
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── entities.py      (has dataclasses)
│   │   └── contracts.py     (overview page contracts)
│   ├── services/
│   │   └── __init__.py
│   ├── templates/
│   └── static/
├── migrations/              (empty — will hold init.sql)
├── seed/                    (empty — will hold seed script)
├── tests/
│   └── __init__.py
├── .env.example             (DB, session, app settings)
├── .gitignore               (configured)
├── Dockerfile               (empty)
├── docker-compose.yml       (empty)
├── pyproject.toml           (all deps with version pins)
├── README.md                (minimal — title, description, tech stack, status)
└── CLAUDE.md                (this file)
```

---

## Data Flow (Agreed Pattern)

```
Browser Request → Uvicorn → FastAPI Router → Service Layer → Database (asyncpg)
                                ↓
                    Jinja2 Template ← pandas aggregation ← raw query results
                                ↓
                    HTML Response → Uvicorn → Browser
```

---

## Git Strategy

- **Convention:** Conventional commits (`type(scope): description`)
- **Branch:** `main` (renamed from master)
- **Branching:** `feat/xxx`, `fix/xxx` per feature, merge to main when complete
- **Reference:** `GIT_GUIDE.md` at Portfolio root (not tracked in this repo)

### Git Log So Far
```
f66a857 chore(init): scaffold project with README, gitignore, app, tests and env template
```

---

## Development Workflow

**Hybrid approach:** Hand-code files that build core understanding. AI-assist files that repeat established patterns.

- **Hand-code** = Helio writes, Claude advises/reviews
- **AI-assisted** = Claude drafts, Helio reviews every line, modifies, and approves

**Decision rule:** Write the first occurrence of every pattern by hand. Once proven, AI-assist the repetitions.

---

## Development Plan

### Phase 1: Planning — DONE
- Entities defined (`entities.py`)
- Overview contracts defined (`contracts.py`)
- Architecture decisions documented
- Project scaffolding committed

### Phase 2: Infrastructure & Docker — ONGOING

| File | Mode | Status |
|---|---|---|
| `app/config.py` | Hand-code | Done |
| `.env.example` | Hand-code | Needs fix (remove `DB_TYPE`) |
| `app/main.py` | Hand-code | In progress |
| `Dockerfile` | AI-assisted | To do |
| `docker-compose.yml` | AI-assisted | To do |

**Milestone:** `docker-compose up` → health endpoint responds

### Phase 3: Database & Seed Data — TO DO

| File | Mode | Status |
|---|---|---|
| `migrations/init.sql` | Hand-code | To do |
| `app/database/connection.py` | Hand-code | To do |
| `seed/seed_data.py` | Hand-code | To do |

**Milestone:** Database starts, schema created, seed data visible via `psql`

### Phase 4: Auth — TO DO

| File | Mode | Status |
|---|---|---|
| `app/auth.py` | Hand-code | To do |
| `app/templates/login.html` | Hand-code | To do |

**Milestone:** Login/logout works, protected routes redirect to `/login`

### Phase 5: Dashboard — Overview Module — TO DO

| File | Mode | Status |
|---|---|---|
| `app/services/overview_service.py` | Hand-code | To do |
| `app/routers/overview_router.py` | Hand-code | To do |
| `app/templates/base.html` | Hand-code | To do |
| `app/templates/components/sidebar.html` | Hand-code | To do |
| `app/templates/components/header.html` | Hand-code | To do |
| `app/templates/overview/summary.html` | Hand-code | To do |
| `app/static/style.css` | AI-assisted | To do |

**Milestone:** Overview page renders with real KPIs and charts from seed data

### Phase 6: Dashboard — Remaining Modules — TO DO

| File | Mode | Status |
|---|---|---|
| `app/services/expenses_service.py` | AI-assisted | To do |
| `app/routers/expenses_router.py` | AI-assisted | To do |
| `app/templates/expenses/*.html` | AI-assisted | To do |
| `app/services/income_service.py` | AI-assisted | To do |
| `app/routers/income_router.py` | AI-assisted | To do |
| `app/templates/income/*.html` | AI-assisted | To do |
| `app/services/budget_service.py` | AI-assisted | To do |
| `app/routers/budget_router.py` | AI-assisted | To do |
| `app/templates/budget/*.html` | AI-assisted | To do |

**Milestone:** All 4 dashboard pages render with data and charts

### Phase 7: Transactions & Export — TO DO

| File | Mode | Status |
|---|---|---|
| `app/routers/transactions_router.py` (POST) | Hand-code | To do |
| `app/routers/transactions_router.py` (GET) | AI-assisted | To do |
| `app/templates/transactions/*.html` | AI-assisted | To do |
| `app/services/export_service.py` | AI-assisted | To do |
| `app/routers/export_router.py` | AI-assisted | To do |

**Milestone:** Can add transactions via form, export CSV

### Phase 8: Tests & Documentation — TO DO

| File | Mode | Status |
|---|---|---|
| `tests/conftest.py` | Hand-code | To do |
| `tests/test_overview_service.py` | Hand-code | To do |
| `tests/test_expenses_service.py` | AI-assisted | To do |
| `tests/test_export_service.py` | AI-assisted | To do |
| `tests/test_transactions.py` | AI-assisted | To do |
| `README.md` (final version) | AI-assisted | To do |

**Milestone:** All tests pass, README has screenshots and setup instructions

---

## Dashboard Pages

| Page | URL | Key Visualizations |
|---|---|---|
| Login | `/login` | Username + password form |
| Overview | `/overview` | KPI cards, income vs expense bar chart, category donut charts, top 5 table |
| Expenses | `/expenses` | Category breakdown, monthly trend line, biggest expenses table |
| Income | `/income` | Source breakdown donut, monthly income bars |
| Budget | `/budget` | Progress bars per category, over/under indicators |
| Transactions | `/transactions` | Filterable table + add transaction form |
| Export | `/export/csv` | CSV file download |

---

## Reference Material (Not Tracked in Git)

- `base/sistemas_dashboard/` — Legacy Bitrix CRM dashboard (study patterns, never copy code/names)
- `planner/IMPLEMENTATION_PLAN.md` — Detailed reference plan (consult if stuck, not a script to follow)
- `CONTEXT.md` / `PROJECT_BRIEF.md` — Project briefs (not in repo)
- `GIT_GUIDE.md` — At Portfolio root, commit conventions and workflow reference