"""Read-side queries for the Transactions list page."""

from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.contracts import (
    CategoryOption,
    TransactionListItem,
    TransactionListResult,
)


async def list_categories(session: AsyncSession) -> list[CategoryOption]:
    query = text("""
        SELECT id, name, type, color
        FROM categories
        ORDER BY type, name
    """)
    result = await session.execute(query)
    return [
        CategoryOption(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            color=row["color"],
        )
        for row in result.mappings().all()
    ]


async def list_transactions(
    session: AsyncSession,
    user_id: int,
    *,
    category_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    type_: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> TransactionListResult:
    # NULL-safe filter pattern: each `(:param IS NULL OR ...)` short-circuits
    # when the bind value is None. COUNT(*) OVER () gives the total matching
    # row count alongside the paged slice — single round trip.
    query = text("""
        SELECT
            t.id AS id,
            t.date AS transaction_date,
            t.description AS description,
            t.amount AS amount,
            c.id AS category_id,
            c.name AS category_name,
            c.color AS category_color,
            c.type AS category_type,
            COUNT(*) OVER () AS total_count
        FROM transactions t
        JOIN categories c ON c.id = t.category_id
        WHERE t.user_id = :user_id
          AND (CAST(:category_id AS INTEGER) IS NULL OR t.category_id = :category_id)
          AND (CAST(:date_from AS DATE) IS NULL OR t.date >= :date_from)
          AND (CAST(:date_to AS DATE) IS NULL OR t.date <= :date_to)
          AND (CAST(:type_ AS TEXT) IS NULL OR c.type = :type_)
        ORDER BY t.date DESC, t.id DESC
        LIMIT :limit OFFSET :offset
    """)
    page = max(1, page)
    offset = (page - 1) * page_size
    result = await session.execute(
        query,
        {
            "user_id": user_id,
            "category_id": category_id,
            "date_from": date_from,
            "date_to": date_to,
            "type_": type_,
            "limit": page_size,
            "offset": offset,
        },
    )
    rows = result.mappings().all()
    total_count = int(rows[0]["total_count"]) if rows else 0
    total_pages = max(1, -(-total_count // page_size))  # ceil division
    items = [
        TransactionListItem(
            id=row["id"],
            transaction_date=row["transaction_date"],
            description=row["description"],
            amount=float(row["amount"]),
            category_id=row["category_id"],
            category_name=row["category_name"],
            category_color=row["category_color"],
            category_type=row["category_type"],
        )
        for row in rows
    ]
    return TransactionListResult(
        items=items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
