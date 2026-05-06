"""Service-layer tests for app.services.transactions_service.create_transaction."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.services.transactions_service import create_transaction


async def test_create_transaction_with_valid_input_inserts_row(seeded_db, test_session):
    cat_result = await test_session.execute(
        text("SELECT id FROM categories WHERE name='Food'")
    )
    cat_id = cat_result.scalar_one()

    new_id = await create_transaction(
        test_session,
        seeded_db,
        amount=Decimal("99.99"),
        category_id=cat_id,
        transaction_date=date(2026, 7, 1),
        description="Service-level insert",
    )
    assert isinstance(new_id, int)
    assert new_id > 0

    # Confirm row visible in the same session
    row = (await test_session.execute(
        text("SELECT amount, description FROM transactions WHERE id = :id"),
        {"id": new_id},
    )).mappings().first()
    assert row is not None
    assert float(row["amount"]) == 99.99
    assert row["description"] == "Service-level insert"


async def test_create_transaction_with_bogus_category_raises_value_error(seeded_db, test_session):
    with pytest.raises(ValueError, match="category"):
        await create_transaction(
            test_session,
            seeded_db,
            amount=Decimal("10.00"),
            category_id=99999,
            transaction_date=date(2026, 7, 1),
            description="Bogus cat",
        )
