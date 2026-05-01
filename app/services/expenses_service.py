"""SQL-first aggregation queries for the Expenses page."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.contracts import (
    CategoryBreakdown,
    ExpenseItem,
    ExpensesPageData,
    MonthlyTotal,
)


async def fetch_expense_breakdown(
    session: AsyncSession, user_id: int, year: int
) -> list[CategoryBreakdown]:
    # Window function gives the grand total across all expense categories
    # for the year — same pattern as Overview's per-month breakdown, but
    # widened to the full year for the donut chart.
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
          AND c.type = 'expense'
        GROUP BY c.name, c.color
        ORDER BY total_amount DESC
    """)
    result = await session.execute(query, {"user_id": user_id, "year": year})
    return [
        CategoryBreakdown(
            name=row["name"],
            color=row["color"],
            type="expense",
            total_amount=float(row["total_amount"]),
            percentage=float(row["percentage"]),
        )
        for row in result.mappings().all()
    ]


async def fetch_monthly_expenses(
    session: AsyncSession, user_id: int, year: int
) -> list[MonthlyTotal]:
    query = text("""
        SELECT
            EXTRACT(MONTH FROM t.date)::int AS month,
            SUM(t.amount) AS total
        FROM transactions t
        JOIN categories c ON c.id = t.category_id
        WHERE t.user_id = :user_id
          AND EXTRACT(YEAR FROM t.date) = :year
          AND c.type = 'expense'
        GROUP BY month
        ORDER BY month
    """)
    result = await session.execute(query, {"user_id": user_id, "year": year})
    return [
        MonthlyTotal(
            month_reference=row["month"],
            year_reference=year,
            amount=float(row["total"]),
            type="expense",
        )
        for row in result.mappings().all()
    ]


async def fetch_top_expenses(
    session: AsyncSession, user_id: int, year: int, limit: int = 10
) -> list[ExpenseItem]:
    query = text("""
        SELECT
            t.date AS transaction_date,
            t.description AS description,
            c.name AS category_name,
            c.color AS category_color,
            t.amount AS amount
        FROM transactions t
        JOIN categories c ON c.id = t.category_id
        WHERE t.user_id = :user_id
          AND EXTRACT(YEAR FROM t.date) = :year
          AND c.type = 'expense'
        ORDER BY t.amount DESC, t.date DESC
        LIMIT :limit
    """)
    result = await session.execute(
        query, {"user_id": user_id, "year": year, "limit": limit}
    )
    return [
        ExpenseItem(
            transaction_date=row["transaction_date"],
            description=row["description"],
            category_name=row["category_name"],
            category_color=row["category_color"],
            amount=float(row["amount"]),
        )
        for row in result.mappings().all()
    ]


async def get_expenses_data(
    session: AsyncSession, user_id: int, year: int
) -> ExpensesPageData:
    return ExpensesPageData(
        year_reference=year,
        monthly_totals=await fetch_monthly_expenses(session, user_id, year),
        category_breakdown=await fetch_expense_breakdown(session, user_id, year),
        top_items=await fetch_top_expenses(session, user_id, year),
    )
