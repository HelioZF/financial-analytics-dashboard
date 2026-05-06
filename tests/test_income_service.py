"""Tests for app.services.income_service against the seeded dataset."""

from app.services.income_service import get_income_data


async def test_breakdown_only_includes_income_categories(seeded_db, test_session):
    data = await get_income_data(test_session, seeded_db, year=2026)
    for c in data.category_breakdown:
        assert c.type == "income"
    # Only Salary in our income seed
    assert [c.name for c in data.category_breakdown] == ["Salary"]


async def test_top_items_returns_only_income_transactions(seeded_db, test_session):
    data = await get_income_data(test_session, seeded_db, year=2026)
    # Seed has 2 income transactions in 2026 (May + June salaries)
    assert len(data.top_items) == 2
    for item in data.top_items:
        assert item.amount == 4000.0
        assert item.category_name == "Salary"


async def test_top_items_sorted_desc(seeded_db, test_session):
    data = await get_income_data(test_session, seeded_db, year=2026)
    amounts = [item.amount for item in data.top_items]
    assert amounts == sorted(amounts, reverse=True)


async def test_year_filter_excludes_other_years(seeded_db, test_session):
    data_2025 = await get_income_data(test_session, seeded_db, year=2025)
    # Seed has 1 income row in 2025 (Salary $4000)
    assert len(data_2025.top_items) == 1
    assert data_2025.top_items[0].transaction_date.year == 2025
    assert data_2025.top_items[0].amount == 4000.0
