# Project 5 — Implementation Plan & Checklist

> **Living document.** Update the checkboxes as work progresses. This is the source of truth for "where are we" — read it before starting any session.

**Last updated:** 2026-05-01
**Current phase:** Step 0 (pre-flight cleanup)
**Commits done:** 0 / 13
**Status:** Planning complete, execution pending green light

---

## Locked decisions (do not revisit unless explicitly asked)

| Decision | Choice | Reasoning |
|---|---|---|
| Mode | Option A — cherry-pick pipeline agents | Project 5 stack diverges too far from pipeline assumptions for full integration |
| Architecture | Layer-based (`services/`, `routers/`, `templates/`) | ADR #5 — proportional to project scope |
| Aggregation strategy | SQL-first (window functions, GROUP BY) | ADR #10 — better portfolio signal for backend roles |
| Charts | Chart.js via CDN | Simpler, no vendoring needed; reverses easily if offline support becomes a concern |
| Style direction | Minimalist (Linear/Vercel-like) | Clean, professional, fast to render; financial data benefits from visual restraint |
| Branch strategy | Direct to `main`, push after every commit | Solo project, low risk, GitHub-visible progress |
| Test gating | No commit unless verification block passes | Quality gate per phase |

---

## How to use this file

- **Each phase has commits, each commit has a verification gate.** Don't commit unless every gate item is checked.
- **Mark `- [x]` as you go.** The next agent/session reads this and knows exactly where to pick up.
- **If you skip a step, leave a comment under the unchecked box** explaining why (e.g., "skipped — already verified in earlier session").
- **Update the status block at top** when finishing a commit (commit count, current phase).
- **Pipeline agent invocations** are noted explicitly — these are the points where Option A cherry-picks from the IA Agents framework.

---

## Step 0 — Pre-flight cleanup

**Goal:** clean working tree, scaffolds removed from existing service.

- [ ] Strip all scaffold blocks from `app/services/overview_service.py` (SQL SHAPE, FUNCTION SHAPE, CONCEPTS, EDGE CASE blocks). Keep only working code + meaningful inline comments.
- [ ] Confirm `app/schemas/contracts.py` has no scaffold leftovers (just imports + dataclasses).
- [ ] Verification: `docker compose exec app python -c "from app.services.overview_service import get_overview_data; print('import OK')"` → expect `import OK`.

---

## Phase 5 — Overview Module

### Commit #1 — `feat(overview): add service layer with SQL-first aggregations`

**Files:**
| File | Status |
|---|---|
| `app/services/overview_service.py` | New (cleaned, post-scaffold) |
| `app/schemas/contracts.py` | Modified (imports added) |

**Verification gate:**
- [ ] Run service assertion script:
  ```bash
  docker compose exec app python -c "
  import asyncio
  from datetime import datetime
  from app.database.connection import SessionLocal
  from app.services.overview_service import get_overview_data

  async def main():
      async with SessionLocal() as s:
          d = await get_overview_data(s, 1, datetime.now().month, datetime.now().year)
          assert d.kpis.total_income > 0
          assert d.kpis.total_expenses > 0
          assert len(d.monthly_data) > 0
          assert len(d.expense_breakdown) > 0
          pct_sum = sum(c.percentage for c in d.expense_breakdown)
          assert 99.0 < pct_sum < 101.0, f'percentages sum to {pct_sum}'
          print('all overview service assertions passed')
  asyncio.run(main())
  "
  ```
  → expect `all overview service assertions passed`
- [ ] All assertions pass (no AssertionError)
- [ ] `git add` only the two files in scope (no accidental includes)
- [ ] `git commit` with message above
- [ ] `git push origin main`

---

### Commit #2 — `feat(overview): add overview page with KPI cards and charts`

**Files:**
| File | Purpose |
|---|---|
| `app/routers/overview_router.py` | `GET /overview`, `require_login` dep, calls `get_overview_data`, renders `summary.html` |
| `app/templates/base.html` | Layout: HTML skeleton, `<head>` (Chart.js CDN + style.css), sidebar block, content block, header block |
| `app/templates/components/sidebar.html` | Nav: overview, expenses, income, budget, transactions, export, logout |
| `app/templates/components/header.html` | Display name + month/year + logout link |
| `app/templates/overview/summary.html` | Extends base; KPI cards row, monthly bar chart, two donut charts, top-5 expenses table |
| `app/static/style.css` | Minimal stylesheet: dark sidebar, light content, KPI grid, chart container sizing |
| `app/main.py` | Modified: include `overview_router`, mount `StaticFiles` for `/static` |

**Verification gate:**
- [ ] `docker compose up` boots clean (no app errors)
- [ ] `curl -i http://localhost:3200/overview` → `302 Location: /login`
- [ ] Browser flow: login as `demo` / `demo123` → redirected to `/overview`
- [ ] DevTools Network: `style.css` returns 200 (not 404)
- [ ] Three KPI cards visible (Income / Expenses / Balance), all non-zero
- [ ] Monthly bar chart shows 12 months
- [ ] Two donut charts render with correct category legends
- [ ] Sidebar shows all nav links (other pages 404 — expected)
- [ ] **Data spot-check:** pick a category from donut, run SQL:
  ```bash
  docker compose exec db psql -U finance_user -d finance -c "
  SELECT c.name, ROUND(SUM(t.amount) / (SELECT SUM(t.amount) FROM transactions t JOIN categories c ON c.id=t.category_id WHERE c.type='expense' AND EXTRACT(MONTH FROM t.date)=EXTRACT(MONTH FROM NOW())) * 100, 2) AS pct
  FROM transactions t JOIN categories c ON c.id=t.category_id
  WHERE c.type='expense' AND EXTRACT(MONTH FROM t.date)=EXTRACT(MONTH FROM NOW())
  GROUP BY c.name ORDER BY pct DESC;"
  ```
  Compare top result to donut legend's top entry. Match required.
- [ ] **Regression:** `/login`, `/logout` still work
- [ ] `git add` files in scope
- [ ] `git commit` with message above
- [ ] `git push origin main`

**🎯 Phase 5 milestone:** `/overview` renders with real numbers from seed data.

---

## Phase 6 — Remaining Dashboard Modules

Each commit = one full page (service + router + template). Same pattern as Phase 5 commit #2.

### Commit #3 — `feat(expenses): add expenses page with category breakdown and monthly trends`

**Files:**
- `app/services/expenses_service.py` — `get_expenses_data(session, user_id, year)`: monthly totals, category breakdown (full year), top-10 individual expenses
- `app/routers/expenses_router.py` — `GET /expenses`, protected
- `app/templates/expenses/summary.html` — donut (category share full year), line chart (12-month trend), top-10 table
- `app/main.py` — include `expenses_router`

**Verification gate:**
- [ ] `/expenses` returns 200 when logged in, 302 to `/login` when not
- [ ] Donut percentages sum to ~100
- [ ] Line chart has 12 data points
- [ ] Top-10 table sorted desc by amount, all rows are expense type
- [ ] **SQL spot-check** on top expense:
  ```sql
  SELECT t.amount, t.description, c.name FROM transactions t JOIN categories c ON c.id=t.category_id
  WHERE c.type='expense' AND EXTRACT(YEAR FROM t.date)=EXTRACT(YEAR FROM NOW())
  ORDER BY t.amount DESC LIMIT 1;
  ```
- [ ] **Regression:** `/overview`, `/login` still work
- [ ] Commit + push

### Commit #4 — `feat(income): add income page with source breakdown and monthly bars`

**Files:** mirror of #3 — `income_service.py`, `income_router.py`, `income/summary.html`.

**Verification gate:**
- [ ] `/income` returns 200 with login, 302 without
- [ ] Donut shows Salary, Freelance, Investments
- [ ] Monthly bars show 12 months
- [ ] **Regression:** `/overview`, `/expenses` still work
- [ ] Commit + push

### Commit #5 — `feat(budget): add budget page with progress bars and over/under indicators`

**Files:**
- `app/services/budget_service.py` — join budgets + transactions per category for current month, compute percent-used + status flag (under/at/over)
- `app/routers/budget_router.py`
- `app/templates/budget/summary.html` — one row per budgeted category with progress bar; over-budget rows visually distinct

**Verification gate:**
- [ ] `/budget` returns 200 with login
- [ ] One row per budgeted category, progress bar visible
- [ ] Over-budget categories have distinct color (red or similar)
- [ ] **SQL spot-check:** pick a category, verify "spent" matches `SUM(amount)` for current month
- [ ] **Regression:** `/overview`, `/expenses`, `/income` still work
- [ ] Commit + push

**🎯 Phase 6 milestone:** all four dashboard pages render with real data.

---

## Phase 7 — Transactions & Export

### Commit #6 — `feat(transactions): add filterable list page`

**Files:**
- `app/services/transactions_service.py` — `list_transactions(session, user_id, filters)` with optional category_id, date_from, date_to, type; paginated
- `app/routers/transactions_router.py` — `GET /transactions` with query params, 50/page
- `app/templates/transactions/list.html` — filter form (GET) + table

**Verification gate:**
- [ ] `/transactions` shows recent 50 by default
- [ ] `?category_id=1` returns only that category's rows
- [ ] `?date_from=YYYY-01-01&date_to=YYYY-01-31` returns only Jan rows of current year
- [ ] Pagination links work (page 2 shows next 50)
- [ ] **Regression:** all dashboard pages still work
- [ ] Commit + push

### Commit #7 — `feat(transactions): add transaction creation form`

**Files:**
- `app/templates/transactions/form.html` — POST form (amount, category select, date, description)
- `app/routers/transactions_router.py` modified — `GET /transactions/new` (form), `POST /transactions/new` (insert + redirect)

**Verification gate:**
- [ ] `/transactions/new` shows form with category dropdown populated from DB
- [ ] Submit valid data → redirects to `/transactions`, new row visible at top
- [ ] Submit invalid data (e.g., negative amount) → re-renders form with error message
- [ ] After submission: `/overview` reflects the new transaction in current-month KPIs
- [ ] **Regression:** all prior pages still work
- [ ] Commit + push

### Commit #8 — `feat(export): add CSV export endpoint`

**Files:**
- `app/services/export_service.py` — `transactions_to_csv(session, user_id)` returns CSV bytes
- `app/routers/export_router.py` — `GET /export/csv` returns `StreamingResponse` with `Content-Disposition: attachment; filename=transactions.csv`
- Sidebar nav: add "Export CSV" link

**Verification gate:**
- [ ] `/export/csv` triggers download in browser (file `transactions.csv`)
- [ ] CSV opens cleanly in Excel/LibreOffice
- [ ] Header row: `id,date,amount,category,type,description`
- [ ] Row count matches `SELECT COUNT(*) FROM transactions WHERE user_id=1`
- [ ] Sample row's amount matches DB exactly
- [ ] Commit + push

**🎯 Phase 7 milestone:** can add transactions, browse/filter them, download CSV.

---

## Phase 8 — Tests, Docs, Polish

> **Pipeline integration:** acting as **QA Agent** for commits 9-11, **Docs Agent** for commit 12.

### Commit #9 — `test: add pytest fixtures and conftest with test db`

**Files:**
- `tests/conftest.py` — async fixtures: ephemeral test DB (separate from dev), seed sample data, async client (`httpx.AsyncClient`), authenticated session helper
- `tests/test_smoke.py` — single test: app starts, `/login` returns 200

**Verification gate:**
- [ ] `docker compose exec app pytest tests/test_smoke.py -v` → 1 passed
- [ ] Test DB doesn't pollute dev DB (verify: dev DB transaction count unchanged after test run)
- [ ] Commit + push

### Commit #10 — `test: add overview, expenses, income, budget service tests`

**Files:**
- `tests/test_overview_service.py` — KPIs assertions, monthly_data shape, breakdown percentages sum to 100, edge case (month with no data → zeros)
- `tests/test_expenses_service.py` — breakdown shape, top-10 ordering, year filter
- `tests/test_income_service.py` — mirror
- `tests/test_budget_service.py` — under/over flags, progress percentages

**Verification gate:**
- [ ] `docker compose exec app pytest tests/ -v` → all pass
- [ ] Coverage spot-check: `pytest --cov=app/services` → ≥70% on services/
- [ ] Commit + push

### Commit #11 — `test: add transactions, export, and auth integration tests`

**Files:**
- `tests/test_transactions.py` — POST /transactions/new (valid + invalid), GET filters, pagination
- `tests/test_export.py` — CSV header + row count + content sample
- `tests/test_auth.py` — login success/fail, protected route redirects, logout clears session

**Verification gate:**
- [ ] `docker compose exec app pytest tests/ -v --cov=app` → all pass
- [ ] Coverage ≥85% on `app/`
- [ ] Commit + push

### Commit #12 — `docs: add README with setup, screenshots, and architecture overview`

**Files:**
- `README.md` — project description, screenshots, setup instructions (`docker compose up`), demo credentials, architecture diagram (mermaid), tech stack table, ADRs summary
- `docs/screenshots/*.png` — overview, expenses, budget, transactions, login (capture manually)
- `docs/ai/system_context.md` — pipeline-style AI context doc (Docs Agent artifact)

**Verification gate:**
- [ ] README renders correctly on GitHub (preview after push)
- [ ] Setup instructions reproducible: fresh clone → `cp .env.example .env` → `docker compose up` → working app
- [ ] All screenshot links resolve
- [ ] Commit + push

### Commit #13 — `chore: drop unused pandas dependency`

**Files:**
- `pyproject.toml` — remove `pandas >=2.2`
- `CLAUDE.md` (gitignored, but update locally) — Tech Stack: remove pandas row; ADR #10: mark pandas as removed

**Verification gate:**
- [ ] Confirm no file imports pandas: `grep -r "import pandas\|from pandas" app/ tests/ seed/` returns nothing
- [ ] `docker compose down -v && docker compose up --build` → full stack boots
- [ ] All routes still work (manual smoke: `/overview`, `/expenses`, `/income`, `/budget`, `/transactions`, `/export/csv`)
- [ ] `pytest tests/ -v` → all still pass
- [ ] Commit + push

**🎯 Phase 8 milestone:** all tests pass, README is portfolio-ready, no dead deps.

---

## Phase 9 — Process Retrospective (no commit)

> **Pipeline integration:** acting as **Process Agent**.

**Output:** `docs/process_improvements/retro_project5.md`

**Content:**
- What worked (cherry-pick of pipeline that actually helped — likely QA Agent + Docs Agent + Process Agent itself)
- What was friction (architectural conflicts with pipeline, mode-flip mid-project, etc.)
- Decisions made mid-flight (data-first, SQL-first, Option A, mode flip)
- Recommendations for Project 6 onboarding
- Suggested adjustments to the IA Agents pipeline (feedback loop into the pipeline repo)

**Tasks:**
- [ ] Draft retro document
- [ ] Review with fresh eyes (next session)
- [ ] Decide whether to commit it to repo or keep local-only
- [ ] If kept local: copy to IA Agents repo as a process improvement input

---

## Cross-cutting standards

| Concern | Standard |
|---|---|
| Commit format | Conventional Commits (`type(scope): description`), first line ≤72 chars, body for context, `Co-Authored-By` trailer |
| Push cadence | After every successful commit |
| Branch | `main` (no feature branches — solo project, low risk) |
| Test gating | No commit unless the phase's verification block passes |
| Regression sweep | Each commit's verification ends with prior-phase smoke check |
| Code style | Match existing — async + asyncpg + raw SQL via `text()`, dataclass contracts, layer-based architecture |
| Comments | Sparse — only WHY-comments where intent isn't obvious. No tutorial scaffolds |
| Error handling | Validate at boundaries (form input, query params); trust internal calls |
| Reviews | Helio reads every diff before commit; no auto-commits |

---

## Progress tracker (update as you go)

| Phase | Commits | Status | Notes |
|---|---|---|---|
| Step 0 | — | ⬜ Not started | Pre-flight cleanup |
| Phase 5 | #1, #2 | ⬜ Not started | Overview module |
| Phase 6 | #3, #4, #5 | ⬜ Not started | Expenses, Income, Budget |
| Phase 7 | #6, #7, #8 | ⬜ Not started | Transactions + Export |
| Phase 8 | #9–#13 | ⬜ Not started | Tests, docs, polish |
| Phase 9 | — | ⬜ Not started | Retrospective artifact |

**Legend:** ⬜ Not started · 🟡 In progress · ✅ Complete · 🛑 Blocked

---

## Quick navigation

- **Resuming work:** scan the Progress tracker → find first ⬜ or 🟡 row → jump to that phase
- **Fresh session:** read this file top to bottom + the latest entry in `docs/audit_log.md` (when it exists)
- **Stuck:** the Pipeline integration notes flag where to invoke an agent role
- **Done with Project 5:** mark all ✅, write Phase 9 retro, hand off to next project's plan

---

*This document was generated 2026-05-01 as the executable plan for Project 5 completion. Update freely as work progresses.*
