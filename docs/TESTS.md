# Project 5 — Test Tracker

> Living document. Mark `[x]` as tests pass; add a brief note with the result.

**Last updated:** 2026-05-04
**Manual verifications run:** 35 / 35 ✅
**Pytest tests planned:** 0 / ~40 (Phase 8 — not started)
**Coverage target:** 80% on `app/` (90%+ on `app/services/`, 70%+ on `app/routers/`)

---

## How this file works

- Each entry is a checkbox: `- [ ]` pending, `- [x]` passing, `- [⚠️]` failing/flaky
- For pytest tests, the entry is the test ID: `tests/test_X.py::test_Y` — runnable directly
- For manual verifications, the entry describes the check and the expected/actual outcome
- When a test passes, tick the box and (if useful) add a short result note in italics
- Update the status block at the top after each session

---

## Section 1 — Manual & automated verifications (historical record)

These are the curl, SQL, and browser checks run during implementation. Each one was a real verification, not a placeholder.

### Phase 5 — Overview Module

**Commit #1 (`92080cd`) — service layer**
- [x] Service assertion script returns expected values *(income=$5,477, expenses=$2,617, balance=$2,860, 24 monthly points, 7 expense categories, percentages sum to 100.00)*
- [x] All `assert` statements in script pass
- [x] Local Python syntax check on `overview_service.py`

**Commit #2 (`b72020e`) — overview page**
- [x] `/overview` unauthenticated → 302 `/login`
- [x] `/overview` authenticated → 200 (9.2KB HTML)
- [x] `/static/style.css` → 200 (StaticFiles mount works)
- [x] `/login` regression → 200
- [x] `/` unauth → 302 `/login`
- [x] Login POST → 302 + session cookie
- [x] HTML markers: 3 KPI cards, monthlyChart/incomeDonut/expenseDonut canvases
- [x] DB ↔ HTML top-5 expenses spot-check *(Rent 45.85%, Food 33.44%, Transport 8.22%, Utilities 7.64%, Shopping 3.71%)*
- [x] Browser visual: KPI values, chart bars, donuts, top-5 table (verified by Helio)

**Bug fix commit (`e344024`)**
- [x] `/overview` h1 = "Overview" (was "Dashboard")
- [x] `/expenses` h1 = "Expenses" (was "Dashboard")
- [x] `/income` h1 = "Income" (was "Dashboard")
- [x] Browser visual: monthly bar chart now renders income (green) + expense (red) bars

### Phase 6 — Remaining dashboard pages

**Commit #3 (`0b7eab4`) — expenses page**
- [x] `/expenses` unauth → 302 `/login`
- [x] `/expenses` auth → 200 (8.7KB)
- [x] categoryDonut and trendChart canvases present
- [x] Top-10 table rows = 10
- [x] DB ↔ HTML top expense spot-check *(Monthly rent · Rent · $1,200.00)*
- [x] Regression: `/overview` still 200
- [x] Browser visual verified

**Commit #4 (`1a35395`) — income page**
- [x] `/income` unauth → 302; auth → 200 (8.0KB)
- [x] sourceDonut and monthlyBars canvases present
- [x] Top-10 table rows = 10
- [x] DB ↔ HTML top income spot-check *(Salary · $4,000.00 · color #2E8B57)*
- [x] Regression: `/overview` and `/expenses` still 200
- [x] Browser visual verified

**Commit #5 (`8f008ef`) — budget page**
- [x] `/budget` unauth → 302; auth → 200
- [x] 8 progress bar rows rendered (one per seeded category)
- [x] Over-budget categories distinct (Food, Transport in red)
- [x] **Cross-page consistency:** Total Spent ($2,617) = `/overview` Expenses KPI
- [x] Regression: `/overview`, `/expenses`, `/income` still 200
- [x] Browser visual verified

### Phase 7 — Transactions & Export

**Commit #6 (`4cc0a71`) — transactions list**
- [x] `/transactions` unauth → 302
- [x] Default load (no params) = full current month → 37 rows for May 2026
- [x] `?category_id=1` → 385 Food transactions across 8 pages
- [x] `?type=income` → 17 rows
- [x] `?date_from=2026-01-01&date_to=2026-01-31` → 47 January rows
- [x] `?date_from=2026-01-01&date_to=2026-12-31` → 621 total, paginated (Page 1 of 13)
- [x] Form fields preserve filter values across submissions
- [x] Pagination prev/next URLs preserve filters
- [x] Regression: all 4 dashboard pages still 200

**Commit #7 (`88fbc8e`) — transaction creation form**
- [x] `/transactions/new` unauth → 302
- [x] GET `/transactions/new` auth → 200 with form, 11 category options grouped Income/Expense
- [x] POST `amount=-50` → 400 with "Amount must be greater than zero."
- [x] POST `category_id=99999` → 400 with "Selected category does not exist."
- [x] POST valid → 303 → `/transactions`, DB count 621→622, row content matches submitted values
- [x] New row visible in `/transactions` list page
- [x] Regression: all 4 dashboard pages still 200
- [x] Browser visual verified (Helio created "ta caro" entry as live test)

**Commit #8 (`34488d3`) — CSV export**
- [x] `/export/csv` unauth → 302
- [x] `/export/csv` auth → 200
- [x] `Content-Type: text/csv; charset=utf-8`
- [x] `Content-Disposition: attachment; filename="transactions_YYYYMMDD.csv"`
- [x] UTF-8 BOM present (first 3 bytes = `EF BB BF`)
- [x] Header row: `id,date,amount,category,type,description`
- [x] Data row count = 622 (matches DB)
- [x] First row exact match vs DB *(id=620, 2026-12-28, $67.00, Health, expense)*
- [x] CSV quoting on comma in description *("Healthcare (doctor, pharmacy)")*
- [x] Sort order: date DESC, id DESC
- [x] Regression: all 6 prior endpoints still 200

---

## Section 2 — Pytest suite (Phase 8 — upcoming)

These are the formal automated tests to be written in commits #9–#11.

### Commit #9 — Fixtures + smoke (foundation)

**`tests/conftest.py` — fixtures**
- [ ] `test_db` fixture: ephemeral test database with `init.sql` applied
- [ ] `test_session` fixture: AsyncSession bound to test_db
- [ ] `seeded_db` fixture: minimal known data (1 user, ~3 categories, ~10 transactions)
- [ ] `async_client` fixture: `httpx.AsyncClient` with `ASGITransport`
- [ ] `authenticated_client` fixture: client with session cookie pre-set

**`tests/test_smoke.py`**
- [ ] `tests/test_smoke.py::test_app_starts` — FastAPI lifespan completes
- [ ] `tests/test_smoke.py::test_login_page_renders` — GET /login → 200
- [ ] `tests/test_smoke.py::test_health_endpoint` — GET /health → 200, `{"status": "ok"}`

### Commit #10 — Service-layer tests

**`tests/test_overview_service.py`**
- [ ] `test_get_overview_data_returns_correct_shape` — all 4 fields populated
- [ ] `test_kpis_balance_equals_income_minus_expenses` — arithmetic invariant
- [ ] `test_breakdown_percentages_sum_to_100` — window-function correctness
- [ ] `test_monthly_data_includes_both_types` — income + expense rows present
- [ ] `test_empty_month_returns_zero_kpis` — no-data edge case (returns 0, not None)
- [ ] `test_unknown_user_returns_empty_lists` — security/isolation

**`tests/test_expenses_service.py`**
- [ ] `test_breakdown_sorted_desc_by_amount`
- [ ] `test_top_items_capped_at_default_limit` (10)
- [ ] `test_top_items_sorted_desc_by_amount_then_date`
- [ ] `test_year_filter_excludes_other_years`
- [ ] `test_empty_year_returns_empty_breakdown`

**`tests/test_income_service.py`**
- [ ] `test_breakdown_sorted_desc_by_amount`
- [ ] `test_top_items_capped_at_default_limit`
- [ ] `test_only_income_type_returned` (no expense rows leak in)
- [ ] `test_year_filter_excludes_other_years`

**`tests/test_budget_service.py`**
- [ ] `test_categories_without_budget_excluded`
- [ ] `test_status_under_when_spent_below_budget`
- [ ] `test_status_over_when_spent_above_budget`
- [ ] `test_percent_used_calculation`
- [ ] `test_total_budgeted_and_spent_match_row_sum`

### Commit #11 — Integration & auth tests

**`tests/test_transactions.py`**
- [ ] `test_list_transactions_no_filters_returns_all`
- [ ] `test_list_transactions_filter_by_category`
- [ ] `test_list_transactions_filter_by_type`
- [ ] `test_list_transactions_filter_by_date_range`
- [ ] `test_list_transactions_pagination_offset_correct`
- [ ] `test_list_transactions_total_count_ignores_limit`
- [ ] `test_create_transaction_valid_input_inserts_row`
- [ ] `test_create_transaction_bogus_category_raises_value_error`
- [ ] `test_post_negative_amount_returns_400_with_form`
- [ ] `test_post_valid_returns_303_to_list`

**`tests/test_export.py`**
- [ ] `test_export_returns_csv_content_type`
- [ ] `test_export_includes_utf8_bom`
- [ ] `test_export_header_row_correct`
- [ ] `test_export_row_count_matches_db`
- [ ] `test_export_quoting_handles_commas_in_description`

**`tests/test_auth.py`**
- [ ] `test_login_with_valid_credentials_sets_cookie`
- [ ] `test_login_with_wrong_password_redirects_with_error`
- [ ] `test_login_with_unknown_user_redirects_with_error`
- [ ] `test_protected_route_without_session_redirects_to_login`
- [ ] `test_logout_clears_session`

---

## Section 3 — Coverage targets

Run after commit #11:
```bash
docker compose exec app pytest tests/ --cov=app --cov-report=term-missing
```

| Module | Target | Notes |
|---|---|---|
| `app/services/` | ≥ 90% | Core business logic; high coverage matters most |
| `app/routers/` | ≥ 70% | Mostly delegation to services; less to test |
| `app/auth.py` | ≥ 85% | Security-sensitive; verify all paths |
| `app/database/` | ≥ 60% | Mostly setup; main concern is `get_session` works |
| **Overall `app/`** | **≥ 80%** | Headline number for portfolio README |

---

## Section 4 — Pre-portfolio manual QA checklist

Run before recording final screenshots / submitting to recruiters:

- [ ] Fresh clone: `git clone` → `cp .env.example .env` → `docker compose up --build` → working app on first try
- [ ] Login with `demo` / `demo123` works
- [ ] All sidebar links navigate to working pages
- [ ] Overview: KPI cards, monthly bar chart, two donuts, top-5 table all render
- [ ] Expenses: donut + line chart + top-10 table render
- [ ] Income: donut + monthly bars + top-10 table render
- [ ] Budget: progress bars render, over-budget rows visually distinct
- [ ] Transactions list: filters work, pagination works, "+ New" button visible
- [ ] Transaction creation form: valid submit redirects to list with row visible
- [ ] Transaction creation form: invalid submit shows error without losing input
- [ ] Export CSV: download triggers, file opens cleanly in Excel/LibreOffice
- [ ] Logout: clears session, returns to /login
- [ ] All chart tooltips show formatted currency
- [ ] No console errors in browser DevTools on any page
- [ ] No 404s on static assets in DevTools Network tab
- [ ] Test "ta caro" entry deleted (or kept, decision made and consistent across screenshots)

---

## Lessons captured

- **`docker compose exec` HTTP checks miss visual bugs.** The page-title block bug (`{% block %}` inside `{% include %}`) and the bar chart 0-width bug both passed automated checks but were caught only on browser inspection. *Future:* always include a browser screenshot step in the verification gate before committing UI changes.
- **CSV row-count assertions catch leftover state.** The 622-vs-621 discrepancy revealed Helio's "ta caro" form entry — useful as a sanity check that the count matches the DB.
- **Cross-page consistency is the cheapest integration test.** "Total Spent on /budget = Expenses KPI on /overview" caught zero bugs but proves all five pages agree on truth.
