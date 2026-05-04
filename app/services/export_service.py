"""CSV export of user transactions, streamed row-by-row."""

import csv
import io
from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


CSV_HEADER = ["id", "date", "amount", "category", "type", "description"]


def _row_to_csv(values: list) -> str:
    """Encode one row as a CSV-formatted string (with newline)."""
    buf = io.StringIO()
    csv.writer(buf).writerow(values)
    return buf.getvalue()


async def transactions_to_csv(
    session: AsyncSession, user_id: int
) -> AsyncIterator[str]:
    """Yield a UTF-8 CSV of every transaction for the user, oldest column first.

    First chunk = UTF-8 BOM + header (so Excel autodetects the encoding).
    Subsequent chunks = one CSV row each, streamed via session.stream() so
    the result set isn't buffered in memory before the response starts.
    """
    yield "﻿" + _row_to_csv(CSV_HEADER)

    query = text("""
        SELECT
            t.id AS id,
            t.date AS date,
            t.amount AS amount,
            c.name AS category,
            c.type AS type,
            t.description AS description
        FROM transactions t
        JOIN categories c ON c.id = t.category_id
        WHERE t.user_id = :user_id
        ORDER BY t.date DESC, t.id DESC
    """)

    stream = await session.stream(query, {"user_id": user_id})
    async for row in stream.mappings():
        yield _row_to_csv([
            row["id"],
            row["date"].isoformat(),
            f"{float(row['amount']):.2f}",
            row["category"],
            row["type"],
            row["description"] or "",
        ])
