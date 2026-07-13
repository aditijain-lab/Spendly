import sqlite3

from database import db as db_module


def _insert_expenses(db_path, user_id, expenses):
    """Insert expense rows directly. expenses is a list of (amount, category) tuples."""
    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            (user_id, amount, category, "2026-07-01", "test expense")
            for amount, category in expenses
        ],
    )
    conn.commit()
    conn.close()


def _set_created_at(db_path, user_id, created_at):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE users SET created_at = ? WHERE id = ?", (created_at, user_id)
    )
    conn.commit()
    conn.close()


def test_get_user_by_id_valid(test_db):
    user_id = test_db.create_user("Demo User", "demo@spendly.com", "pw")
    _set_created_at(test_db.DB_PATH, user_id, "2026-01-15 10:00:00")

    result = test_db.get_user_by_id(user_id)

    assert result["name"] == "Demo User"
    assert result["email"] == "demo@spendly.com"
    assert result["member_since"] == "January 2026"


def test_get_user_by_id_not_found(test_db):
    result = test_db.get_user_by_id(999999)
    assert result is None


def test_get_user_by_id_initials(test_db):
    user_id = test_db.create_user("Demo User", "demo2@spendly.com", "pw")
    result = test_db.get_user_by_id(user_id)
    assert result["initials"] == "DU"

    single_id = test_db.create_user("Madonna", "madonna@spendly.com", "pw")
    result_single = test_db.get_user_by_id(single_id)
    assert result_single["initials"] == "M"


def test_get_summary_stats_with_expenses(test_db):
    user_id = test_db.create_user("Demo User", "demo3@spendly.com", "pw")
    expenses = [
        (450.00, "Food"),
        (150.00, "Transport"),
        (1200.00, "Bills"),
        (600.00, "Health"),
        (250.00, "Entertainment"),
        (899.00, "Shopping"),
        (100.00, "Other"),
        (320.50, "Food"),
    ]
    _insert_expenses(test_db.DB_PATH, user_id, expenses)

    result = test_db.get_summary_stats(user_id)

    assert result["total_spent"] == 3969.50
    assert result["transaction_count"] == 8
    assert result["top_category"] == "Bills"


def test_get_summary_stats_no_expenses(test_db):
    user_id = test_db.create_user("No Expenses", "noexp@spendly.com", "pw")

    result = test_db.get_summary_stats(user_id)

    assert result == {"total_spent": 0, "transaction_count": 0, "top_category": "-"}
