import os
import sqlite3
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

# Anchor to the project root (one level up from this file) so the DB
# always lands in the same place regardless of the process's cwd.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "expense_tracker.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()

    existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing > 0:
        conn.close()
        return

    password_hash = generate_password_hash("demo123")
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash),
    )
    user_id = cursor.lastrowid

    expenses = [
        (user_id, 450.00, "Food", "2026-07-01", "Groceries at supermarket"),
        (user_id, 150.00, "Transport", "2026-07-02", "Fuel for car"),
        (user_id, 1200.00, "Bills", "2026-07-02", "Electricity bill"),
        (user_id, 600.00, "Health", "2026-07-03", "Doctor consultation"),
        (user_id, 250.00, "Entertainment", "2026-07-04", "Movie tickets"),
        (user_id, 899.00, "Shopping", "2026-07-05", "New shoes"),
        (user_id, 100.00, "Other", "2026-07-06", "Miscellaneous expense"),
        (user_id, 320.50, "Food", "2026-07-07", "Dinner with friends"),
    ]

    conn.executemany(
        """
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        expenses,
    )
    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return user


def verify_user(email, password):
    user = get_user_by_email(email)
    if user is None:
        return None
    if not check_password_hash(user["password_hash"], password):
        return None
    return user


def create_user(name, email, password):
    conn = get_db()
    password_hash = generate_password_hash(password)
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def create_expense(user_id, amount, category, date, description):
    """Insert a new expense row for user_id and return its new id."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, date, description),
    )
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    return expense_id


def _date_range_clause(start_date, end_date):
    """Return (sql_fragment, params_list). Empty if either date is missing."""
    if start_date and end_date:
        return " AND date BETWEEN ? AND ?", [start_date, end_date]
    return "", []


def get_recent_transactions(user_id, limit=10, start_date=None, end_date=None):
    """Return list of dicts (date, description, category, amount), newest-first."""
    conn = get_db()
    clause, params = _date_range_clause(start_date, end_date)
    rows = conn.execute(
        "SELECT date, description, category, amount FROM expenses "
        "WHERE user_id = ?" + clause + " ORDER BY date DESC, id DESC LIMIT ?",
        [user_id, *params, limit],
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_user_by_id(user_id):
    """Return dict with name, email, member_since, initials, or None if not found."""
    conn = get_db()
    row = conn.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    name = row["name"]
    dt = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
    words = name.split()
    initials = "".join(w[0] for w in words[:2]).upper() if words else ""
    return {
        "name": name,
        "email": row["email"],
        "member_since": dt.strftime("%B %Y"),
        "initials": initials,
    }


def get_summary_stats(user_id, start_date=None, end_date=None):
    """Return dict with total_spent (float), transaction_count (int), top_category (str)."""
    conn = get_db()
    clause, params = _date_range_clause(start_date, end_date)
    total_row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt "
        "FROM expenses WHERE user_id = ?" + clause,
        [user_id, *params],
    ).fetchone()
    top_row = conn.execute(
        "SELECT category, SUM(amount) AS cat_total FROM expenses "
        "WHERE user_id = ?" + clause + " GROUP BY category ORDER BY cat_total DESC LIMIT 1",
        [user_id, *params],
    ).fetchone()
    conn.close()
    return {
        "total_spent": total_row["total"],
        "transaction_count": total_row["cnt"],
        "top_category": top_row["category"] if top_row else "-",
    }


def get_category_breakdown(user_id, start_date=None, end_date=None):
    """Return list of dicts (name, total, bar_pct), ordered by total desc.
    bar_pct is bucketed to the nearest multiple of 5 in [0, 100]."""
    conn = get_db()
    clause, params = _date_range_clause(start_date, end_date)
    rows = conn.execute(
        "SELECT category, SUM(amount) AS cat_total FROM expenses "
        "WHERE user_id = ?" + clause + " GROUP BY category ORDER BY cat_total DESC",
        [user_id, *params],
    ).fetchall()
    conn.close()
    if not rows:
        return []
    grand_total = sum(r["cat_total"] for r in rows)
    result = []
    for r in rows:
        pct = (r["cat_total"] / grand_total) * 100 if grand_total else 0
        bar_pct = max(0, min(100, round(pct / 5) * 5))
        result.append({
            "name": r["category"],
            "total": r["cat_total"],
            "bar_pct": bar_pct,
        })
    return result
