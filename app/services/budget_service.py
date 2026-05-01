"""SQL-first aggregation queries for the Budget page."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.contracts import BudgetPageData, BudgetRow


async def fetch_budget_rows(
    session: AsyncSession, user_id: int, month: int, year: int
) -> list[BudgetRow]:
    # LEFT JOIN budgets -> transactions on the same category and month/year.
    # COALESCE handles "budgeted but nothing spent yet" (left side has no match).
    # Categories without a budget are excluded by design — page is about
    # budget tracking, so unbudgeted categories don't belong here.
    query = text("""
        SELECT
            c.name AS name,
            c.color AS color,
            b.amount AS budgeted,
            COALESCE(SUM(t.amount), 0) AS spent
        FROM budgets b
        JOIN categories c ON c.id = b.category_id
        LEFT JOIN transactions t
            ON t.category_id = b.category_id
            AND t.user_id = b.user_id
            AND EXTRACT(MONTH FROM t.date) = b.month
            AND EXTRACT(YEAR FROM t.date) = b.year
        WHERE b.user_id = :user_id
          AND b.month = :month
          AND b.year = :year
        GROUP BY c.name, c.color, b.amount
        ORDER BY b.amount DESC
    """)
    result = await session.execute(
        query, {"user_id": user_id, "month": month, "year": year}
    )
    rows: list[BudgetRow] = []
    for row in result.mappings().all():
        budgeted = float(row["budgeted"])
        spent = float(row["spent"])
        # Defensive against zero budgets (shouldn't happen with seed data,
        # but the schema allows it).
        percent_used = (spent / budgeted * 100) if budgeted > 0 else 0
        status = "over" if spent > budgeted else "under"
        rows.append(
            BudgetRow(
                category_name=row["name"],
                category_color=row["color"],
                budgeted=budgeted,
                spent=spent,
                percent_used=percent_used,
                status=status,
            )
        )
    return rows


async def get_budget_data(
    session: AsyncSession, user_id: int, month: int, year: int
) -> BudgetPageData:
    rows = await fetch_budget_rows(session, user_id, month, year)
    return BudgetPageData(
        month_reference=month,
        year_reference=year,
        rows=rows,
        total_budgeted=sum(r.budgeted for r in rows),
        total_spent=sum(r.spent for r in rows),
    )
