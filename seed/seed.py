import asyncio
import random
from datetime import datetime
from decimal import Decimal

import bcrypt
from sqlalchemy import text

from app.database.connection import SessionLocal


EXPENSE_CATEGORIES = [
    ("Food", "#FF6384"),
    ("Transport", "#36A2EB"),
    ("Rent", "#FFCE56"),
    ("Entertainment", "#4BC0C0"),
    ("Health", "#9966FF"),
    ("Utilities", "#FF9F40"),
    ("Shopping", "#C9CBCF"),
    ("Education", "#68FF63"),
]

INCOME_CATEGORIES = [
    ("Salary", "#2E8B57"),
    ("Freelance", "#CA1594"),
    ("Investments", "#00008B"),
]

NARRATIVE_ARC = {
    1: "post-holiday overspending, negative balance",
    2: "tight budget, rent + food dominate",
    3: "unexpected car repair (Transport spike)",
    4: "medical emergency (Health spike)",
    5: "freelance gig in month 5, extra income",
    6: "normal month, balanced spending",
    7: "summer vacation (Entertainment spike)",
    8: "back-to-school shopping (Shopping spike)",
    9: "utilities spike (air conditioning in summer)",
    10: "freelance slowdown, tight month",
    11: "normal month, balanced spending",
    12: "holiday overspending, negative balance",
}


def hash_password(plain_password: str) -> str:
    hashed_bytes = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed_bytes.decode("utf-8")


def gen_month(year, month, user_id, category_ids, arc_note) -> list[dict]:
    transactions = []

    transactions.append({
        "user_id": user_id,
        "category_id": category_ids["Salary"],
        "amount": Decimal("4000.00"),
        "date": datetime(year, month, 1),
        "description": "Monthly salary",
    })

    freelance_months = [5]
    if month in freelance_months:
        transactions.append({
            "user_id": user_id,
            "category_id": category_ids["Freelance"],
            "amount": Decimal(random.randint(500, 1500)),
            "date": datetime(year, month, 15),
            "description": "Freelance gig",
        })

    investment_months = [3, 6, 9, 12]
    if month in investment_months:
        transactions.append({
            "user_id": user_id,
            "category_id": category_ids["Investments"],
            "amount": Decimal(random.randint(100, 300)),
            "date": datetime(year, month, 20),
            "description": "Investment returns",
        })

    transactions.append({
        "user_id": user_id,
        "category_id": category_ids["Rent"],
        "amount": Decimal("1200.00"),
        "date": datetime(year, month, 5),
        "description": "Monthly rent",
    })

    for _ in range(random.randint(20, 40)):
        transactions.append({
            "user_id": user_id,
            "category_id": category_ids["Food"],
            "amount": Decimal(random.randint(15, 80)),
            "date": datetime(year, month, random.randint(1, 28)),
            "description": "Grocery/restaurant",
        })

    for _ in range(random.randint(8, 15)):
        transactions.append({
            "user_id": user_id,
            "category_id": category_ids["Transport"],
            "amount": Decimal(random.randint(5, 50)),
            "date": datetime(year, month, random.randint(1, 28)),
            "description": "Transportation (gas, rideshare, public transit)",
        })

    utilities_amounts = [Decimal("100.00"), Decimal("50.00"), Decimal("50.00")]
    for i in range(random.randint(2, 3)):
        transactions.append({
            "user_id": user_id,
            "category_id": category_ids["Utilities"],
            "amount": utilities_amounts[i],
            "date": datetime(year, month, random.randint(1, 28)),
            "description": "Utilities",
        })

    entertainment_amount = (
        Decimal(random.randint(50, 200))
        if "Entertainment spike" in arc_note
        else Decimal(random.randint(10, 50))
    )
    transactions.append({
        "user_id": user_id,
        "category_id": category_ids["Entertainment"],
        "amount": entertainment_amount,
        "date": datetime(year, month, random.randint(1, 28)),
        "description": "Entertainment",
    })

    health_amount = (
        Decimal("500.00")
        if "Health spike" in arc_note
        else Decimal(random.randint(20, 80))
    )
    transactions.append({
        "user_id": user_id,
        "category_id": category_ids["Health"],
        "amount": health_amount,
        "date": datetime(year, month, random.randint(1, 28)),
        "description": "Healthcare (doctor, pharmacy)",
    })

    shopping_amount = (
        Decimal("400.00")
        if "Shopping spike" in arc_note
        else Decimal(random.randint(30, 100))
    )
    transactions.append({
        "user_id": user_id,
        "category_id": category_ids["Shopping"],
        "amount": shopping_amount,
        "date": datetime(year, month, random.randint(1, 28)),
        "description": "Shopping",
    })

    if random.random() < 0.3:
        transactions.append({
            "user_id": user_id,
            "category_id": category_ids["Education"],
            "amount": Decimal(random.randint(20, 100)),
            "date": datetime(year, month, random.randint(1, 28)),
            "description": "Education (books, courses)",
        })

    return transactions


def gen_budgets(year, month, user_id, category_ids) -> list[dict]:
    category_budgets = {
        "Rent": Decimal("1200.00"),
        "Food": Decimal("500.00"),
        "Transport": Decimal("200.00"),
        "Entertainment": Decimal("150.00"),
        "Health": Decimal("100.00"),
        "Utilities": Decimal("200.00"),
        "Shopping": Decimal("300.00"),
        "Education": Decimal("50.00"),
    }
    return [
        {
            "user_id": user_id,
            "category_id": category_ids[name],
            "amount": amount,
            "month": month,
            "year": year,
        }
        for name, amount in category_budgets.items()
    ]


async def main():
    async with SessionLocal() as session:
        result = await session.execute(
            text("SELECT id FROM users WHERE username = :u"),
            {"u": "demo"},
        )
        if result.scalar_one_or_none() is not None:
            print("Database already seeded, skipping.")
            return

        result = await session.execute(
            text(
                "INSERT INTO users (username, display_name, password_hash) "
                "VALUES (:u, :d, :p) RETURNING id"
            ),
            {"u": "demo", "d": "Demo User", "p": hash_password("demo123")},
        )
        user_id = result.scalar_one()

        category_ids = {}
        for categories, cat_type in [
            (EXPENSE_CATEGORIES, "expense"),
            (INCOME_CATEGORIES, "income"),
        ]:
            for name, color in categories:
                result = await session.execute(
                    text(
                        "INSERT INTO categories (type, color, name) "
                        "VALUES (:t, :c, :n) RETURNING id"
                    ),
                    {"t": cat_type, "c": color, "n": name},
                )
                category_ids[name] = result.scalar_one()

        current_year = datetime.now().year

        all_transactions = []
        for month in range(1, 13):
            arc_note = NARRATIVE_ARC.get(month, "")
            all_transactions.extend(
                gen_month(current_year, month, user_id, category_ids, arc_note)
            )
        await session.execute(
            text(
                "INSERT INTO transactions (user_id, category_id, amount, date, description) "
                "VALUES (:user_id, :category_id, :amount, :date, :description)"
            ),
            all_transactions,
        )

        all_budgets = []
        for month in range(1, 13):
            all_budgets.extend(
                gen_budgets(current_year, month, user_id, category_ids)
            )
        await session.execute(
            text(
                "INSERT INTO budgets (user_id, category_id, amount, month, year) "
                "VALUES (:user_id, :category_id, :amount, :month, :year)"
            ),
            all_budgets,
        )

        await session.commit()
        print(
            f"Seeded {len(all_transactions)} transactions "
            f"and {len(all_budgets)} budgets."
        )


if __name__ == "__main__":
    asyncio.run(main())
