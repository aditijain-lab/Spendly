import sqlite3


SEED_EXPENSES = [
    (450.00, "Food", "2026-07-01", "Groceries at supermarket"),
    (150.00, "Transport", "2026-07-02", "Fuel for car"),
    (1200.00, "Bills", "2026-07-02", "Electricity bill"),
    (600.00, "Health", "2026-07-03", "Doctor consultation"),
    (250.00, "Entertainment", "2026-07-04", "Movie tickets"),
    (899.00, "Shopping", "2026-07-05", "New shoes"),
    (100.00, "Other", "2026-07-06", "Miscellaneous expense"),
    (320.50, "Food", "2026-07-07", "Dinner with friends"),
]


def _insert_expenses(test_db, user_id, expenses):
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


def test_get_recent_transactions_returns_all_seed_rows_newest_first(test_db):
    user_id = test_db.create_user("Demo User", "demo@spendly.com", "demo123")
    _insert_expenses(test_db, user_id, SEED_EXPENSES)

    result = test_db.get_recent_transactions(user_id)

    assert len(result) == 8
    assert result[0]["date"] == "2026-07-07"


def test_get_recent_transactions_no_expenses_returns_empty_list(test_db):
    user_id = test_db.create_user("No Expenses", "noexpenses@spendly.com", "demo123")

    result = test_db.get_recent_transactions(user_id)

    assert result == []


def test_get_recent_transactions_respects_limit(test_db):
    user_id = test_db.create_user("Demo User", "demo@spendly.com", "demo123")
    _insert_expenses(test_db, user_id, SEED_EXPENSES)

    result = test_db.get_recent_transactions(user_id, limit=3)

    assert len(result) == 3
    assert result[0]["date"] == "2026-07-07"


def test_get_recent_transactions_includes_both_july_2_rows(test_db):
    user_id = test_db.create_user("Demo User", "demo@spendly.com", "demo123")
    _insert_expenses(test_db, user_id, SEED_EXPENSES)

    result = test_db.get_recent_transactions(user_id)
    categories_on_july_2 = {row["category"] for row in result if row["date"] == "2026-07-02"}

    assert categories_on_july_2 == {"Bills", "Transport"}


def test_get_recent_transactions_row_keys_are_exact(test_db):
    user_id = test_db.create_user("Demo User", "demo@spendly.com", "demo123")
    _insert_expenses(test_db, user_id, SEED_EXPENSES)

    result = test_db.get_recent_transactions(user_id)

    for row in result:
        assert set(row.keys()) == {"date", "description", "category", "amount"}
