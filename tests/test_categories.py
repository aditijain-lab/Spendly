import sqlite3

from database import db as db_module


def _insert_expenses(test_db, user_id, expenses):
    """expenses: list of (amount, category, date, description)."""
    conn = sqlite3.connect(test_db.DB_PATH)
    conn.executemany(
        """
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        [(user_id, amount, category, date, description)
         for amount, category, date, description in expenses],
    )
    conn.commit()
    conn.close()


def test_category_breakdown_seed_like_data(test_db):
    user_id = test_db.create_user("Demo User", "demo@spendly.com", "demo123")
    _insert_expenses(test_db, user_id, [
        (450.00, "Food", "2026-07-01", "Groceries at supermarket"),
        (150.00, "Transport", "2026-07-02", "Fuel for car"),
        (1200.00, "Bills", "2026-07-02", "Electricity bill"),
        (600.00, "Health", "2026-07-03", "Doctor consultation"),
        (250.00, "Entertainment", "2026-07-04", "Movie tickets"),
        (899.00, "Shopping", "2026-07-05", "New shoes"),
        (100.00, "Other", "2026-07-06", "Miscellaneous expense"),
        (320.50, "Food", "2026-07-07", "Dinner with friends"),
    ])

    result = db_module.get_category_breakdown(user_id)

    assert len(result) == 7
    names_totals = [(r["name"], r["total"]) for r in result]
    assert names_totals == [
        ("Bills", 1200.00),
        ("Shopping", 899.00),
        ("Food", 770.50),
        ("Health", 600.00),
        ("Entertainment", 250.00),
        ("Transport", 150.00),
        ("Other", 100.00),
    ]


def test_bar_pct_is_multiple_of_5_within_range(test_db):
    user_id = test_db.create_user("Demo User", "demo@spendly.com", "demo123")
    _insert_expenses(test_db, user_id, [
        (450.00, "Food", "2026-07-01", "Groceries at supermarket"),
        (150.00, "Transport", "2026-07-02", "Fuel for car"),
        (1200.00, "Bills", "2026-07-02", "Electricity bill"),
        (600.00, "Health", "2026-07-03", "Doctor consultation"),
        (250.00, "Entertainment", "2026-07-04", "Movie tickets"),
        (899.00, "Shopping", "2026-07-05", "New shoes"),
        (100.00, "Other", "2026-07-06", "Miscellaneous expense"),
        (320.50, "Food", "2026-07-07", "Dinner with friends"),
    ])

    result = db_module.get_category_breakdown(user_id)

    for item in result:
        assert item["bar_pct"] % 5 == 0
        assert 0 <= item["bar_pct"] <= 100


def test_name_field_preserves_raw_category_casing(test_db):
    user_id = test_db.create_user("Demo User", "demo@spendly.com", "demo123")
    _insert_expenses(test_db, user_id, [
        (450.00, "Food", "2026-07-01", "Groceries at supermarket"),
        (150.00, "Transport", "2026-07-02", "Fuel for car"),
    ])

    result = db_module.get_category_breakdown(user_id)

    names = [r["name"] for r in result]
    assert "Food" in names
    assert "food" not in names


def test_no_expenses_returns_empty_list(test_db):
    user_id = test_db.create_user("Lonely User", "lonely@spendly.com", "pw123")

    result = db_module.get_category_breakdown(user_id)

    assert result == []


def test_single_category_returns_one_entry_full_bar(test_db):
    user_id = test_db.create_user("Single Cat User", "single@spendly.com", "pw123")
    _insert_expenses(test_db, user_id, [
        (100.00, "Food", "2026-07-01", "Lunch"),
        (200.00, "Food", "2026-07-02", "Dinner"),
    ])

    result = db_module.get_category_breakdown(user_id)

    assert len(result) == 1
    assert result[0]["name"] == "Food"
    assert result[0]["total"] == 300.00
    assert result[0]["bar_pct"] == 100
