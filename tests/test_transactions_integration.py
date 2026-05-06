"""HTTP-level integration tests for the /transactions routes."""

from sqlalchemy import text


async def _seed_food_category(SessionLocal) -> int:
    async with SessionLocal() as session:
        await session.execute(
            text("INSERT INTO categories (name, type, color) VALUES (:n, :t, :c)"),
            {"n": "Food", "t": "expense", "c": "#FF6384"},
        )
        await session.commit()
        result = await session.execute(text("SELECT id FROM categories WHERE name='Food'"))
        return result.scalar_one()


async def test_post_negative_amount_returns_400_with_form_error(authed_client, app_with_test_db):
    cat_id = await _seed_food_category(app_with_test_db)

    response = await authed_client.post(
        "/transactions/new",
        data={
            "amount": "-50",
            "category_id": str(cat_id),
            "transaction_date": "2026-06-15",
            "description": "Bad amount",
        },
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert "Amount must be greater than zero" in response.text


async def test_post_valid_creates_row_and_redirects(authed_client, app_with_test_db):
    SessionLocal = app_with_test_db
    cat_id = await _seed_food_category(SessionLocal)

    response = await authed_client.post(
        "/transactions/new",
        data={
            "amount": "42.50",
            "category_id": str(cat_id),
            "transaction_date": "2026-06-15",
            "description": "Valid POST",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/transactions"

    # Verify the row landed in the test DB
    async with SessionLocal() as session:
        row = (await session.execute(
            text("SELECT amount, description FROM transactions WHERE description = 'Valid POST'")
        )).mappings().first()
        assert row is not None
        assert float(row["amount"]) == 42.50


async def test_get_transactions_list_renders(authed_client, app_with_test_db):
    """GET /transactions returns 200 even with no rows (empty-state copy)."""
    response = await authed_client.get("/transactions", follow_redirects=False)
    assert response.status_code == 200
    # Empty-state copy from list.html
    assert "No transactions match these filters" in response.text or "0 transaction" in response.text
