"""Tests for app.services.expenses_service against the seeded dataset."""

from app.services.expenses_service import get_expenses_data


async def test_breakdown_sorted_desc_by_amount(seeded_db, test_session):
    data = await get_expenses_data(test_session, seeded_db, year=2026)
    amounts = [c.total_amount for c in data.category_breakdown]
    assert amounts == sorted(amounts, reverse=True)
    # Year totals: Rent 2400, Food 425, Transport 50 (Salary excluded)
    names = [c.name for c in data.category_breakdown]
    assert names == ["Rent", "Food", "Transport"]


async def test_breakdown_only_includes_expense_categories(seeded_db, test_session):
    data = await get_expenses_data(test_session, seeded_db, year=2026)
    for c in data.category_breakdown:
        assert c.type == "expense"
    assert "Salary" not in [c.name for c in data.category_breakdown]


async def test_top_items_capped_at_default_limit(seeded_db, test_session):
    data = await get_expenses_data(test_session, seeded_db, year=2026)
    # Seed has 6 expense transactions in 2026 (under the 10-item cap)
    assert len(data.top_items) == 6
    for item in data.top_items:
        assert item.transaction_date.year == 2026


async def test_top_items_sorted_desc_by_amount(seeded_db, test_session):
    data = await get_expenses_data(test_session, seeded_db, year=2026)
    amounts = [item.amount for item in data.top_items]
    assert amounts == sorted(amounts, reverse=True)
    # The two $1200 Rent rows tie at the top
    assert data.top_items[0].amount == 1200.0
    assert data.top_items[1].amount == 1200.0


async def test_year_filter_excludes_other_years(seeded_db, test_session):
    data_2025 = await get_expenses_data(test_session, seeded_db, year=2025)
    # Only one expense row in 2025: Food $50
    assert len(data_2025.top_items) == 1
    assert data_2025.top_items[0].transaction_date.year == 2025
    assert data_2025.top_items[0].amount == 50.0
    # Breakdown should also only contain Food
    assert [c.name for c in data_2025.category_breakdown] == ["Food"]
