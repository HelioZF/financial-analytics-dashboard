"""SQL-first aggregation queries for the Overview page.

Each function returns a piece of OverviewPageData. Postgres does the heavy
lifting (GROUP BY, window functions); Python only maps rows into dataclasses.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.contracts import (
    CategoryBreakdown,
    MonthlyTotal,
    OverviewKPIs,
    OverviewPageData,
)


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
    result = await session.execute(
        query, {"user_id": user_id, "year": year, "month": month}
    )
    # GROUP BY returns no row for a category type that has zero transactions
    # this month, so missing keys default to 0 below.
    totals = {row["type"]: float(row["total"]) for row in result.mappings().all()}
    income = totals.get("income", 0)
    expenses = totals.get("expense", 0)
    return OverviewKPIs(
        month_reference=month,
        year_reference=year,
        total_income=income,
        total_expenses=expenses,
        total_balance=income - expenses,
    )


async def fetch_monthly_totals(
    session: AsyncSession, user_id: int, year: int
) -> list[MonthlyTotal]:
    # ::int cast — EXTRACT returns numeric, which asyncpg surfaces as Decimal.
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


async def fetch_breakdown(
    session: AsyncSession, user_id: int, month: int, year: int, type_: str
) -> list[CategoryBreakdown]:
    # Window function `SUM(SUM(...)) OVER ()` computes the grand total across
    # all groups in one pass — avoids a self-join or subquery for the percentage.
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
    result = await session.execute(
        query,
        {"user_id": user_id, "month": month, "year": year, "type": type_},
    )
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


async def get_overview_data(
    session: AsyncSession, user_id: int, month: int, year: int
) -> OverviewPageData:
    return OverviewPageData(
        kpis=await fetch_kpis(session, user_id, month, year),
        monthly_data=await fetch_monthly_totals(session, user_id, year),
        income_breakdown=await fetch_breakdown(session, user_id, month, year, "income"),
        expense_breakdown=await fetch_breakdown(session, user_id, month, year, "expense"),
    )
