"""
Tests for Step 6: Date Filter For Profile Page.

Spec: .claude/specs/06-date-filter-profile-page.md

These tests define the expected behavior of the `start_date` / `end_date`
query-string filter on GET /profile (and the underlying db.py helpers) as a
correctness contract derived from the spec — not from the implementation.
"""

import importlib
import re
import sqlite3

import pytest

from database import db as db_module


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Isolated DB for testing database/db.py helpers directly."""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", str(db_path))
    db_module.init_db()
    return db_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Isolated DB + Flask test client for testing the /profile route."""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", str(db_path))

    import app as app_module

    importlib.reload(app_module)
    app_module.app.config.update(TESTING=True)

    with app_module.app.test_client() as test_client:
        yield test_client


def _insert_expenses(db_path, user_id, expenses):
    """expenses: list of (amount, category, date, description) tuples."""
    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            (user_id, amount, category, date, description)
            for amount, category, date, description in expenses
        ],
    )
    conn.commit()
    conn.close()


def _register(client, name, email, password="password123"):
    """Register a new user via the test client. Registration logs the user in.
    Returns the new user's id (note: seed_db() pre-populates a demo user, so
    ids are not guaranteed to start at 1 -- always use the returned id)."""
    client.post(
        "/register", data={"name": name, "email": email, "password": password}
    )
    with client.session_transaction() as sess:
        return sess["user_id"]


def _input_value(body, field_name):
    """Extract the value="..." attribute of the named <input> in the rendered HTML,
    or None if not found / empty."""
    match = re.search(
        r'name="%s"[^>]*value="([^"]*)"' % re.escape(field_name), body
    )
    if match is None:
        return None
    return match.group(1) or None


# Distinct, well-separated dates so inclusive-boundary and range tests are unambiguous.
DATED_EXPENSES = [
    (100.00, "Food", "2026-07-01", "Groceries"),
    (200.00, "Transport", "2026-07-05", "Cab ride"),
    (300.00, "Bills", "2026-07-10", "Electricity"),
    (400.00, "Health", "2026-07-15", "Checkup"),
]
FULL_TOTAL = sum(amount for amount, *_ in DATED_EXPENSES)  # 1000.00
FULL_COUNT = len(DATED_EXPENSES)  # 4


# ==================================================================== #
# DB-layer tests: database/db.py helpers accept start_date/end_date
# ==================================================================== #

class TestGetSummaryStatsDateFilter:
    def test_filtered_range_totals_only_matching_expenses(self, test_db):
        """Spec: valid start_date/end_date filters Total Spent / Transactions /
        Top Category to the inclusive range."""
        user_id = test_db.create_user("Demo User", "demo@spendly.com", "pw")
        _insert_expenses(test_db.DB_PATH, user_id, DATED_EXPENSES)

        result = test_db.get_summary_stats(
            user_id, start_date="2026-07-05", end_date="2026-07-10"
        )

        assert result["total_spent"] == 500.00, "should sum only Transport + Bills"
        assert result["transaction_count"] == 2
        assert result["top_category"] == "Bills"

    def test_range_boundaries_are_inclusive(self, test_db):
        """Spec: filter range is inclusive on both ends."""
        user_id = test_db.create_user("Demo User", "demo@spendly.com", "pw")
        _insert_expenses(test_db.DB_PATH, user_id, DATED_EXPENSES)

        result = test_db.get_summary_stats(
            user_id, start_date="2026-07-01", end_date="2026-07-01"
        )

        assert result["total_spent"] == 100.00
        assert result["transaction_count"] == 1
        assert result["top_category"] == "Food"

    def test_no_params_returns_all_time_data(self, test_db):
        """Spec: no params -> same all-time data as before."""
        user_id = test_db.create_user("Demo User", "demo@spendly.com", "pw")
        _insert_expenses(test_db.DB_PATH, user_id, DATED_EXPENSES)

        result = test_db.get_summary_stats(user_id)

        assert result["total_spent"] == FULL_TOTAL
        assert result["transaction_count"] == FULL_COUNT

    def test_empty_result_range_returns_zeroed_stats(self, test_db):
        """Spec: filtering to a range with no matching expenses -> ₹0 total,
        0 transactions, no errors."""
        user_id = test_db.create_user("Demo User", "demo@spendly.com", "pw")
        _insert_expenses(test_db.DB_PATH, user_id, DATED_EXPENSES)

        result = test_db.get_summary_stats(
            user_id, start_date="2026-08-01", end_date="2026-08-31"
        )

        assert result == {"total_spent": 0, "transaction_count": 0, "top_category": "-"}


class TestGetRecentTransactionsDateFilter:
    def test_filtered_range_returns_only_matching_rows(self, test_db):
        user_id = test_db.create_user("Demo User", "demo@spendly.com", "pw")
        _insert_expenses(test_db.DB_PATH, user_id, DATED_EXPENSES)

        result = test_db.get_recent_transactions(
            user_id, start_date="2026-07-05", end_date="2026-07-10"
        )

        dates = {row["date"] for row in result}
        assert dates == {"2026-07-05", "2026-07-10"}
        assert len(result) == 2

    def test_range_boundaries_are_inclusive(self, test_db):
        user_id = test_db.create_user("Demo User", "demo@spendly.com", "pw")
        _insert_expenses(test_db.DB_PATH, user_id, DATED_EXPENSES)

        result = test_db.get_recent_transactions(
            user_id, start_date="2026-07-01", end_date="2026-07-15"
        )

        assert len(result) == FULL_COUNT, "range spanning all dates inclusively returns all rows"

    def test_empty_result_range_returns_empty_list(self, test_db):
        user_id = test_db.create_user("Demo User", "demo@spendly.com", "pw")
        _insert_expenses(test_db.DB_PATH, user_id, DATED_EXPENSES)

        result = test_db.get_recent_transactions(
            user_id, start_date="2026-08-01", end_date="2026-08-31"
        )

        assert result == []


class TestGetCategoryBreakdownDateFilter:
    def test_filtered_range_includes_only_matching_categories(self, test_db):
        user_id = test_db.create_user("Demo User", "demo@spendly.com", "pw")
        _insert_expenses(test_db.DB_PATH, user_id, DATED_EXPENSES)

        result = test_db.get_category_breakdown(
            user_id, start_date="2026-07-05", end_date="2026-07-10"
        )

        names = {r["name"] for r in result}
        assert names == {"Transport", "Bills"}
        assert "Food" not in names
        assert "Health" not in names

    def test_filtered_totals_sum_to_filtered_grand_total(self, test_db):
        """Spec DoD: category breakdown percentages still sum to 100% of the
        filtered range -- verified via the underlying totals reconciling with
        the filtered summary stats total."""
        user_id = test_db.create_user("Demo User", "demo@spendly.com", "pw")
        _insert_expenses(test_db.DB_PATH, user_id, DATED_EXPENSES)

        stats = test_db.get_summary_stats(
            user_id, start_date="2026-07-05", end_date="2026-07-10"
        )
        breakdown = test_db.get_category_breakdown(
            user_id, start_date="2026-07-05", end_date="2026-07-10"
        )

        assert sum(r["total"] for r in breakdown) == stats["total_spent"]

    def test_empty_result_range_returns_empty_list(self, test_db):
        user_id = test_db.create_user("Demo User", "demo@spendly.com", "pw")
        _insert_expenses(test_db.DB_PATH, user_id, DATED_EXPENSES)

        result = test_db.get_category_breakdown(
            user_id, start_date="2026-08-01", end_date="2026-08-31"
        )

        assert result == []


class TestDateFilterUserIsolation:
    """Spec: filtering must never leak another user's expenses -- the existing
    WHERE user_id = ? clause stays in every query."""

    def test_overlapping_date_ranges_do_not_leak_between_users(self, test_db):
        user_a = test_db.create_user("User A", "a@spendly.com", "pw")
        user_b = test_db.create_user("User B", "b@spendly.com", "pw")

        _insert_expenses(
            test_db.DB_PATH,
            user_a,
            [(50.00, "Food", "2026-07-05", "A's lunch")],
        )
        _insert_expenses(
            test_db.DB_PATH,
            user_b,
            [(9999.00, "Bills", "2026-07-05", "B's huge bill")],
        )

        stats_a = test_db.get_summary_stats(
            user_a, start_date="2026-07-01", end_date="2026-07-10"
        )
        transactions_a = test_db.get_recent_transactions(
            user_a, start_date="2026-07-01", end_date="2026-07-10"
        )
        categories_a = test_db.get_category_breakdown(
            user_a, start_date="2026-07-01", end_date="2026-07-10"
        )

        assert stats_a["total_spent"] == 50.00, "user A's total must not include user B's expense"
        assert stats_a["transaction_count"] == 1
        assert all(t["description"] != "B's huge bill" for t in transactions_a)
        assert all(c["name"] != "Bills" or c["total"] != 9999.00 for c in categories_a)


# ==================================================================== #
# Route-layer tests: GET /profile with start_date/end_date query params
# ==================================================================== #

class TestProfileDateFilterAuthGuard:
    def test_unauthenticated_get_without_filter_redirects_to_login(self, client):
        response = client.get("/profile")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_unauthenticated_get_with_filter_params_redirects_to_login(self, client):
        response = client.get(
            "/profile?start_date=2026-07-01&end_date=2026-07-31"
        )
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


class TestProfileDateFilterHappyPath:
    def test_no_params_shows_all_time_data(self, client):
        user_id = _register(client, "Demo User", "filtertest@spendly.com")
        _insert_expenses(
            db_module.DB_PATH,
            user_id,
            DATED_EXPENSES,
        )

        response = client.get("/profile")
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "₹1,000.00" in body
        for _, category, _, _ in DATED_EXPENSES:
            assert category in body
        assert "Clear filter" not in body

    def test_valid_range_filters_stats_transactions_and_categories(self, client):
        user_id = _register(client, "Demo User", "filtertest@spendly.com")
        _insert_expenses(db_module.DB_PATH, user_id, DATED_EXPENSES)

        response = client.get(
            "/profile?start_date=2026-07-05&end_date=2026-07-10"
        )
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "₹500.00" in body, "Total Spent should reflect only the filtered range"
        assert "Transport" in body
        assert "Bills" in body
        assert "Groceries" not in body, "expense outside the range must not appear"
        assert "Checkup" not in body, "expense outside the range must not appear"

    def test_valid_range_inputs_are_prefilled_after_reload(self, client):
        user_id = _register(client, "Demo User", "filtertest@spendly.com")
        _insert_expenses(db_module.DB_PATH, user_id, DATED_EXPENSES)

        response = client.get(
            "/profile?start_date=2026-07-05&end_date=2026-07-10"
        )
        body = response.get_data(as_text=True)

        assert _input_value(body, "start_date") == "2026-07-05"
        assert _input_value(body, "end_date") == "2026-07-10"

    def test_clear_filter_link_visible_when_filter_active(self, client):
        user_id = _register(client, "Demo User", "filtertest@spendly.com")
        _insert_expenses(db_module.DB_PATH, user_id, DATED_EXPENSES)

        response = client.get(
            "/profile?start_date=2026-07-05&end_date=2026-07-10"
        )
        body = response.get_data(as_text=True)

        assert "Clear filter" in body

    def test_clear_filter_link_points_to_profile_with_no_query_params(self, client):
        user_id = _register(client, "Demo User", "filtertest@spendly.com")
        _insert_expenses(db_module.DB_PATH, user_id, DATED_EXPENSES)

        response = client.get(
            "/profile?start_date=2026-07-05&end_date=2026-07-10"
        )
        body = response.get_data(as_text=True)

        match = re.search(r'href="([^"]*)"[^>]*>\s*Clear filter', body)
        assert match is not None, "expected a 'Clear filter' link in the response"
        href = match.group(1)
        assert href.rstrip("/").endswith("/profile"), f"unexpected clear-filter href: {href}"
        assert "?" not in href, "clear filter link must not carry query params"

    def test_empty_result_range_shows_zeroed_state_without_errors(self, client):
        user_id = _register(client, "Demo User", "filtertest@spendly.com")
        _insert_expenses(db_module.DB_PATH, user_id, DATED_EXPENSES)

        response = client.get(
            "/profile?start_date=2026-08-01&end_date=2026-08-31"
        )
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "₹0.00" in body
        assert '<span class="stat-value">0</span>' in body
        for _, category, _, _ in DATED_EXPENSES:
            assert category not in body, "no category rows should render for an empty range"
        assert "Clear filter" in body, "filter is still 'active' (valid, well-formed range)"


class TestProfileDateFilterFallbackToUnfiltered:
    """Spec: only one date supplied, start_date after end_date, or invalid date
    formats must all be treated as unfiltered with no error (no 500)."""

    @pytest.mark.parametrize(
        "query_string",
        [
            pytest.param("start_date=2026-07-05", id="only_start_date"),
            pytest.param("end_date=2026-07-10", id="only_end_date"),
            pytest.param(
                "start_date=2026-07-10&end_date=2026-07-05", id="start_after_end"
            ),
            pytest.param(
                "start_date=not-a-date&end_date=2026-07-10", id="invalid_start_format"
            ),
            pytest.param(
                "start_date=2026-07-05&end_date=07/10/2026", id="invalid_end_format"
            ),
            pytest.param(
                "start_date=2026-13-40&end_date=2026-07-10", id="nonexistent_date"
            ),
        ],
    )
    def test_falls_back_to_unfiltered_all_time_data(self, client, query_string):
        user_id = _register(client, "Demo User", "filtertest@spendly.com")
        _insert_expenses(db_module.DB_PATH, user_id, DATED_EXPENSES)

        response = client.get(f"/profile?{query_string}")
        body = response.get_data(as_text=True)

        assert response.status_code == 200, "invalid/partial filter must never 500"
        assert "₹1,000.00" in body, "should show the all-time total, not a filtered one"
        for _, category, _, _ in DATED_EXPENSES:
            assert category in body
        assert "Clear filter" not in body, "an ignored filter is not an 'active' filter"


class TestProfileDateFilterUserIsolation:
    def test_second_users_expenses_never_appear_in_filtered_results(self, client):
        user_a_id = _register(client, "User A", "a@spendly.com")
        _insert_expenses(
            db_module.DB_PATH, user_a_id, [(50.00, "Food", "2026-07-05", "A's lunch")]
        )

        client.get("/logout")

        user_b_id = _register(client, "User B", "b@spendly.com")
        _insert_expenses(
            db_module.DB_PATH, user_b_id, [(9999.00, "Bills", "2026-07-05", "B's huge bill")]
        )

        # Currently logged in as User B; filter over the same overlapping range.
        response = client.get(
            "/profile?start_date=2026-07-01&end_date=2026-07-10"
        )
        body = response.get_data(as_text=True)

        assert "₹9,999.00" in body
        assert "A's lunch" not in body
        assert "₹50.00" not in body
