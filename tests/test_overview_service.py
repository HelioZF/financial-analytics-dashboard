"""Tests for app.services.overview_service against the seeded dataset."""

from app.services.overview_service import get_overview_data


async def test_get_overview_data_returns_correct_shape(seeded_db, test_session):
    data = await get_overview_data(test_session, seeded_db, month=6, year=2026)
    assert data.kpis is not None
    assert isinstance(data.monthly_data, list)
    assert isinstance(data.income_breakdown, list)
    assert isinstance(data.expense_breakdown, list)


async def test_kpis_balance_equals_income_minus_expenses(seeded_db, test_session):
    data = await get_overview_data(test_session, seeded_db, month=6, year=2026)
    # June 2026: income $4000, expenses 100+75+1200+50 = $1425
    assert data.kpis.total_income == 4000.0
    assert data.kpis.total_expenses == 1425.0
    assert data.kpis.total_balance == 2575.0
    assert data.kpis.month_reference == 6
    assert data.kpis.year_reference == 2026


async def test_breakdown_percentages_sum_to_100(seeded_db, test_session):
    data = await get_overview_data(test_session, seeded_db, month=6, year=2026)
    pct_sum = sum(c.percentage for c in data.expense_breakdown)
    assert 99.99 <= pct_sum <= 100.01  # tolerance for ROUND in SQL


async def test_monthly_data_includes_both_types_for_seeded_months(seeded_db, test_session):
    data = await get_overview_data(test_session, seeded_db, month=6, year=2026)
    types_seen = {(m.month_reference, m.type) for m in data.monthly_data}
    assert (5, "income") in types_seen
    assert (5, "expense") in types_seen
    assert (6, "income") in types_seen
    assert (6, "expense") in types_seen


async def test_empty_month_returns_zero_kpis(seeded_db, test_session):
    # December has no seed data
    data = await get_overview_data(test_session, seeded_db, month=12, year=2026)
    assert data.kpis.total_income == 0
    assert data.kpis.total_expenses == 0
    assert data.kpis.total_balance == 0
    assert data.expense_breakdown == []
    assert data.income_breakdown == []


async def test_unknown_user_returns_empty_results(seeded_db, test_session):
    data = await get_overview_data(test_session, user_id=99999, month=6, year=2026)
    assert data.kpis.total_income == 0
    assert data.kpis.total_expenses == 0
    assert data.monthly_data == []
    assert data.expense_breakdown == []
    assert data.income_breakdown == []
