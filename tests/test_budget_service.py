"""Tests for app.services.budget_service against the seeded dataset."""

from app.services.budget_service import get_budget_data


async def test_only_budgeted_categories_appear(seeded_db, test_session):
    data = await get_budget_data(test_session, seeded_db, month=6, year=2026)
    names = {row.category_name for row in data.rows}
    # Budgets exist for Food, Rent, Transport (not Salary)
    assert names == {"Food", "Rent", "Transport"}


async def test_status_under_when_spent_below_budget(seeded_db, test_session):
    data = await get_budget_data(test_session, seeded_db, month=6, year=2026)
    food = next(r for r in data.rows if r.category_name == "Food")
    # Food: budgeted $200, spent $175 (100 + 75) → under
    assert food.budgeted == 200.0
    assert food.spent == 175.0
    assert food.status == "under"


async def test_status_over_when_spent_above_budget(seeded_db, test_session):
    data = await get_budget_data(test_session, seeded_db, month=6, year=2026)
    transport = next(r for r in data.rows if r.category_name == "Transport")
    # Transport: budgeted $30, spent $50 → over
    assert transport.budgeted == 30.0
    assert transport.spent == 50.0
    assert transport.status == "over"


async def test_percent_used_calculation(seeded_db, test_session):
    data = await get_budget_data(test_session, seeded_db, month=6, year=2026)
    food = next(r for r in data.rows if r.category_name == "Food")
    # 175 / 200 * 100 = 87.5
    assert abs(food.percent_used - 87.5) < 0.01


async def test_total_budgeted_and_spent_match_row_sum(seeded_db, test_session):
    data = await get_budget_data(test_session, seeded_db, month=6, year=2026)
    # Budgeted: 200 + 1200 + 30 = 1430
    assert data.total_budgeted == 1430.0
    # Spent: 175 (Food) + 1200 (Rent) + 50 (Transport) = 1425
    assert data.total_spent == 1425.0
