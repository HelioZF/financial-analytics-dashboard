"""HTTP-level integration tests for /export/csv."""

from datetime import date

from sqlalchemy import text


async def test_export_returns_csv_content_type(authed_client):
    response = await authed_client.get("/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]


async def test_export_includes_utf8_bom(authed_client):
    response = await authed_client.get("/export/csv")
    # First three bytes are the UTF-8 BOM
    assert response.content[:3] == b"\xef\xbb\xbf"


async def test_export_row_count_matches_db(authed_client, app_with_test_db):
    SessionLocal = app_with_test_db

    # Seed: 1 category + 3 transactions for the demo user (already inserted by
    # demo_user_in_db -> authed_client chain)
    async with SessionLocal() as session:
        await session.execute(
            text("INSERT INTO categories (name, type, color) VALUES (:n, :t, :c)"),
            {"n": "Food", "t": "expense", "c": "#FF6384"},
        )
        await session.commit()
        cat_id = (await session.execute(text("SELECT id FROM categories WHERE name='Food'"))).scalar_one()
        user_id = (await session.execute(text("SELECT id FROM users WHERE username='demo'"))).scalar_one()
        for i in range(3):
            await session.execute(
                text(
                    "INSERT INTO transactions "
                    "(user_id, category_id, amount, date, description) "
                    "VALUES (:u, :c, 10.00, :d, :desc)"
                ),
                {"u": user_id, "c": cat_id, "d": date(2026, 6, 1 + i), "desc": f"Test {i}"},
            )
        await session.commit()

    response = await authed_client.get("/export/csv")
    body = response.text
    # BOM is on the same line as the header. Splitting on \n gives:
    #   header line, 3 data lines, possibly empty trailing
    lines = [line for line in body.splitlines() if line.strip()]
    assert len(lines) == 4  # 1 header + 3 data rows
    # Header sanity
    assert lines[0].endswith("id,date,amount,category,type,description")
