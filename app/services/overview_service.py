# ============================================================================
# overview_service.py
# ============================================================================
# PURPOSE
#   The data pipeline for the Overview page. Given a user_id + month + year,
#   produces an `OverviewPageData` object that the router hands to the template.
#
# APPROACH (SQL-first, decided 2026-04-22)
#   Each piece of the OverviewPageData contract gets its own focused SQL query.
#   Postgres does the aggregation; Python just maps rows into dataclasses.
#   No pandas, no in-memory post-processing.
#
# WHY SQL-first
#   - Portfolio signal for backend roles: multi-table joins, GROUP BY, window
#     functions are the baseline expectation. Showcasing them directly is
#     clearer than wrapping them in pandas.
#   - Performance: database engines are optimized for aggregations. You pull
#     already-aggregated rows (tens of rows), not every raw transaction.
#   - Fewer layers: rows come out of SQL in the shape you want.
# ============================================================================


from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.contracts import (
    OverviewKPIs,
    MonthlyTotal,
    CategoryBreakdown,
    OverviewPageData,
)


# ============================================================================
# SECTION 1 — KPIs for a specific month
# ============================================================================
# OUTPUT: OverviewKPIs(month_reference, year_reference, total_income, total_expenses, total_balance)
#
# SQL STRATEGY
#   One query that returns total amount grouped by category type ('income' or 'expense'),
#   filtered to the target user + month + year. That's 0, 1, or 2 rows back.
#   Python handles the "balance = income - expenses" arithmetic afterwards.
#
# SQL SHAPE
#   SELECT c.type, COALESCE(SUM(t.amount), 0) AS total
#   FROM transactions t
#   JOIN categories c ON c.id = t.category_id
#   WHERE t.user_id = :user_id
#     AND EXTRACT(YEAR FROM t.date) = :year
#     AND EXTRACT(MONTH FROM t.date) = :month
#   GROUP BY c.type
#
# EDGE CASE
#   If the user has zero transactions for the month, the query returns ZERO rows
#   (not "income: 0, expense: 0"). Your Python code must default both sides to 0
#   when the key is missing. A simple dict with .get(..., 0) handles this.
#
# FUNCTION SHAPE
async def fetch_kpis(
    session: AsyncSession, user_id: int, month: int, year: int
) -> OverviewKPIs:
    query = text("""
                SELECT c.type, SUM(t.amount) AS total
                FROM transactions t
                JOIN categories c ON c.id = t.category_id
                WHERE t.user_id = :user_id
                AND EXTRACT(YEAR FROM t.date) = :year
                AND EXTRACT(MONTH FROM t.date) = :month
                GROUP BY c.type
                """)
    
    result = await session.execute(query, {"user_id": user_id, "year": year, "month": month})
    rows = result.mappings().all()
    totals = {row["type"]: float(row["total"]) for row in rows}
    income = totals.get("income", 0)
    expenses = totals.get("expense", 0)
    return OverviewKPIs(
        month_reference=month,
        year_reference=year,
        total_income=income,
        total_expenses=expenses,
        total_balance=income - expenses,
    )


# ============================================================================
# SECTION 2 — Monthly totals for the bar chart (full year, grouped by month+type)
# ============================================================================
# OUTPUT: List[MonthlyTotal] — one row per (month, type) that has activity
#
# SQL STRATEGY
#   Group by month-number AND category type for the whole year. Postgres returns
#   rows like: (1, 'income', 4000), (1, 'expense', 2500), (2, 'income', 4000), ...
#
# SQL SHAPE
#   SELECT
#       EXTRACT(MONTH FROM t.date)::int AS month,
#       c.type AS type,
#       SUM(t.amount) AS total
#   FROM transactions t
#   JOIN categories c ON c.id = t.category_id
#   WHERE t.user_id = :user_id
#     AND EXTRACT(YEAR FROM t.date) = :year
#   GROUP BY month, c.type
#   ORDER BY month, c.type
#
# NOTE on EXTRACT
#   EXTRACT(MONTH FROM date) returns a `numeric` in Postgres. The `::int` cast
#   keeps it as a Python int coming out of asyncpg. Skip the cast and you'll
#   get a Decimal — harmless but ugly.
#
# DESIGN QUESTION FOR YOU
#   A month with zero activity will be MISSING from the result (not a zero row).
#   For a bar chart a missing January would look like a rendering bug. Two options:
#     (a) Let the template handle missing months by iterating 1..12 and looking
#         up each month in a dict built from the rows. Simple.
#     (b) Fill gaps in SQL using generate_series(1, 12) LEFT JOIN'd to the
#         aggregation. More advanced — a nice "look what I can do" moment, and a
#         real portfolio signal. Worth trying once you have (a) working.
#   Ping me when you're ready and I'll explain the generate_series pattern.
#
# FUNCTION SHAPE
async def fetch_monthly_totals(
    session: AsyncSession, user_id: int, year: int
) -> list[MonthlyTotal]:
    
    query = text("""
                SELECT
                    EXTRACT(MONTH FROM t.date)::int AS month,
                    c.type AS type,
                    SUM(t.amount) AS total
                FROM transactions t
                JOIN categories c ON c.id = t.category_id
                WHERE t.user_id = :user_id
                AND EXTRACT(YEAR FROM t.date) = :year
                GROUP BY month, c.type
                ORDER BY month, c.type
                """)
    
    result = await session.execute(query, {"user_id": user_id, "year": year})
    return [
        MonthlyTotal(
            month_reference=row["month"],
            year_reference=year,
            amount=float(row["total"]),
            type=row["type"],
        )
        for row in result.mappings().all()
    ]


# ============================================================================
# SECTION 3 — Category breakdowns for the donut charts
# ============================================================================
# OUTPUT: List[CategoryBreakdown] — per-category totals + percentage, for a
#         specific month and specific type (income OR expense).
#
# SQL STRATEGY — USE A WINDOW FUNCTION
#   To compute "percentage of total" you need two things per row:
#     - this category's sum
#     - the grand total of all categories in the result set
#   A window function computes the grand total WITHOUT a self-join or subquery.
#   This is the kind of SQL that reviewers notice.
#
# SQL SHAPE
#   SELECT
#       c.name AS name,
#       c.color AS color,
#       SUM(t.amount) AS total_amount,
#       ROUND(
#           SUM(t.amount) * 100.0 / SUM(SUM(t.amount)) OVER (),
#           2
#       ) AS percentage
#   FROM transactions t
#   JOIN categories c ON c.id = t.category_id
#   WHERE t.user_id = :user_id
#     AND EXTRACT(YEAR FROM t.date) = :year
#     AND EXTRACT(MONTH FROM t.date) = :month
#     AND c.type = :type
#   GROUP BY c.name, c.color
#   ORDER BY total_amount DESC
#
# KEY PIECE TO UNDERSTAND
#   `SUM(SUM(t.amount)) OVER ()` — the inner SUM is the regular GROUP BY
#   aggregation (per category). The outer SUM is a window aggregation with
#   an EMPTY OVER () clause, meaning "sum across the entire result set".
#   That gives you the grand total on every row. Divide one by the other
#   and you have the percentage.
#
# EDGE CASE
#   Zero matching rows → empty list returned. The SQL handles this naturally:
#   no groups means no rows in the result, which means the list comprehension
#   yields an empty list. No division-by-zero possible because the window
#   function only runs when there are rows.
#
# FUNCTION SHAPE
async def fetch_breakdown(
    session: AsyncSession, user_id: int, month: int, year: int, type_: str
) -> list[CategoryBreakdown]:
    
    query = text("""
                SELECT
                    c.name AS name,
                    c.color AS color,
                    SUM(t.amount) AS total_amount,
                    ROUND(
                        SUM(t.amount) * 100.0 / SUM(SUM(t.amount)) OVER (),
                        2
                    ) AS percentage
                FROM transactions t
                JOIN categories c ON c.id = t.category_id
                WHERE t.user_id = :user_id
                AND EXTRACT(YEAR FROM t.date) = :year
                AND EXTRACT(MONTH FROM t.date) = :month
                AND c.type = :type
                GROUP BY c.name, c.color
                ORDER BY total_amount DESC
                """)
    
    result = await session.execute(query, {"user_id": user_id, "month": month, "year": year, "type": type_})
    return [
        CategoryBreakdown(
            name=row["name"],
            color=row["color"],
            type=type_,
            total_amount=float(row["total_amount"]),
            percentage=float(row["percentage"]),
        )
        for row in result.mappings().all()
    ]


# ============================================================================
# SECTION 4 — Top-level composer: the single entry point the router will call
# ============================================================================
# OUTPUT: OverviewPageData — all four pieces wired together.
#
# PERFORMANCE NOTE (you don't need to act on this, but worth seeing)
#   Each fetch_* function is an independent await. You can run them in parallel
#   with asyncio.gather(...) for a small latency win:
#     kpis, monthly, inc, exp = await asyncio.gather(
#         fetch_kpis(...), fetch_monthly_totals(...),
#         fetch_breakdown(..., "income"), fetch_breakdown(..., "expense"),
#     )
#   BUT: asyncpg connections from the same SQLAlchemy session cannot run queries
#   concurrently on the same session. You'd need four separate sessions to make
#   this actually parallel. For this project's scale, sequential is fine and
#   simpler. Mentioning so you know the concept exists.
#
# FUNCTION SHAPE (sequential version — start here)
async def get_overview_data(
    session: AsyncSession, user_id: int, month: int, year: int
) -> OverviewPageData:
    return OverviewPageData(
        kpis=await fetch_kpis(session, user_id, month, year),
        monthly_data=await fetch_monthly_totals(session, user_id, year),
        income_breakdown=await fetch_breakdown(session, user_id, month, year, "income"),
        expense_breakdown=await fetch_breakdown(session, user_id, month, year, "expense"),
    )


# ============================================================================
# HOW TO MANUALLY TEST THIS BEFORE WRITING THE ROUTER
# ============================================================================
# Once you've hand-coded the functions above, sanity-check the output without
# a browser by running a one-off script inside the container:
#
#   docker compose exec app python -c "
#   import asyncio
#   from datetime import datetime
#   from app.database.connection import SessionLocal
#   from app.services.overview_service import get_overview_data
#
#   async def main():
#       async with SessionLocal() as s:
#           data = await get_overview_data(
#               s, user_id=1, month=datetime.now().month, year=datetime.now().year
#           )
#           print('KPIs:', data.kpis)
#           print('Monthly points:', len(data.monthly_data))
#           print('Expense categories:', len(data.expense_breakdown))
#   asyncio.run(main())
#   "
#
# Confirm shape + numbers look right BEFORE wiring templates. Templates should
# consume a known-good object.
