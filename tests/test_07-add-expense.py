"""
Tests for Step 7: Add Expense.

Spec: .claude/specs/07-add-expense.md

These tests define the expected behavior of GET/POST /expenses/add and the
underlying database/db.py `create_expense` helper as a correctness contract
derived from the spec -- not from the implementation.
"""

import importlib
import re

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
    """Isolated DB + Flask test client for testing the /expenses/add route."""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", str(db_path))

    import app as app_module

    importlib.reload(app_module)
    app_module.app.config.update(TESTING=True)

    with app_module.app.test_client() as test_client:
        yield test_client


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


ALLOWED_CATEGORIES = [
    "Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other",
]

VALID_EXPENSE = {
    "amount": "250.50",
    "category": "Food",
    "date": "2026-07-20",
    "description": "Test lunch",
}


# ==================================================================== #
# DB-layer tests: database/db.py create_expense helper
# ==================================================================== #

class TestCreateExpense:
    def test_inserts_row_with_correct_values(self, test_db):
        user_id = test_db.create_user("Demo User", "addexpensetest@spendly.com", "pw")

        expense_id = test_db.create_expense(
            user_id, 250.50, "Food", "2026-07-20", "Test lunch"
        )

        assert expense_id is not None
        transactions = test_db.get_recent_transactions(user_id, limit=10)
        assert len(transactions) == 1
        row = transactions[0]
        assert row["date"] == "2026-07-20"
        assert row["description"] == "Test lunch"
        assert row["category"] == "Food"
        assert row["amount"] == 250.50

    def test_allows_empty_description(self, test_db):
        user_id = test_db.create_user("Demo User", "addexpensetest@spendly.com", "pw")

        test_db.create_expense(user_id, 75.0, "Other", "2026-07-18", "")

        transactions = test_db.get_recent_transactions(user_id, limit=10)
        assert transactions[0]["description"] == ""

    def test_new_expense_reflected_in_summary_stats(self, test_db):
        user_id = test_db.create_user("Demo User", "addexpensetest@spendly.com", "pw")

        test_db.create_expense(user_id, 100.0, "Food", "2026-07-01", "a")
        test_db.create_expense(user_id, 50.0, "Food", "2026-07-02", "b")

        stats = test_db.get_summary_stats(user_id)
        assert stats["total_spent"] == 150.0
        assert stats["transaction_count"] == 2

    def test_new_expense_reflected_in_category_breakdown(self, test_db):
        user_id = test_db.create_user("Demo User", "addexpensetest@spendly.com", "pw")

        test_db.create_expense(user_id, 100.0, "Bills", "2026-07-01", "a")

        breakdown = test_db.get_category_breakdown(user_id)
        names = {c["name"] for c in breakdown}
        assert "Bills" in names


# ==================================================================== #
# Route-layer tests: GET /expenses/add
# ==================================================================== #

class TestAddExpenseAuthGuard:
    def test_get_while_logged_out_redirects_to_login(self, client):
        response = client.get("/expenses/add")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_post_while_logged_out_redirects_to_login(self, client):
        response = client.post("/expenses/add", data=VALID_EXPENSE)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_post_while_logged_out_does_not_create_expense(self, client):
        client.post("/expenses/add", data=VALID_EXPENSE)

        # No user was ever created/logged in, so nothing should exist to check
        # against -- register a user afterwards and confirm they have no expenses.
        user_id = _register(client, "Demo User", "later@spendly.com")
        transactions = db_module.get_recent_transactions(user_id)
        assert transactions == []


class TestAddExpenseGetHappyPath:
    def test_get_while_logged_in_returns_200(self, client):
        _register(client, "Demo User", "addexpensetest@spendly.com")

        response = client.get("/expenses/add")

        assert response.status_code == 200

    def test_get_form_has_empty_amount_and_description(self, client):
        _register(client, "Demo User", "addexpensetest@spendly.com")

        response = client.get("/expenses/add")
        body = response.get_data(as_text=True)

        assert _input_value(body, "amount") is None
        assert _input_value(body, "description") is None

    def test_get_form_date_defaults_to_today(self, client):
        import datetime as dt

        _register(client, "Demo User", "addexpensetest@spendly.com")

        response = client.get("/expenses/add")
        body = response.get_data(as_text=True)

        today = dt.datetime.now().strftime("%Y-%m-%d")
        assert _input_value(body, "date") == today

    def test_get_form_lists_all_allowed_categories(self, client):
        _register(client, "Demo User", "addexpensetest@spendly.com")

        response = client.get("/expenses/add")
        body = response.get_data(as_text=True)

        for category in ALLOWED_CATEGORIES:
            assert category in body


# ==================================================================== #
# Route-layer tests: POST /expenses/add -- happy path
# ==================================================================== #

class TestAddExpensePostHappyPath:
    def test_valid_submission_redirects_to_profile(self, client):
        _register(client, "Demo User", "addexpensetest@spendly.com")

        response = client.post("/expenses/add", data=VALID_EXPENSE)

        assert response.status_code == 302
        assert "/profile" in response.headers["Location"]

    def test_valid_submission_creates_expense_for_current_user(self, client):
        user_id = _register(client, "Demo User", "addexpensetest@spendly.com")

        client.post("/expenses/add", data=VALID_EXPENSE)

        transactions = db_module.get_recent_transactions(user_id)
        assert len(transactions) == 1
        assert transactions[0]["description"] == "Test lunch"
        assert transactions[0]["category"] == "Food"
        assert transactions[0]["amount"] == 250.50

    def test_valid_submission_appears_on_profile_page(self, client):
        _register(client, "Demo User", "addexpensetest@spendly.com")

        client.post("/expenses/add", data=VALID_EXPENSE)
        response = client.get("/profile")
        body = response.get_data(as_text=True)

        assert "Test lunch" in body
        assert "₹250.50" in body

    def test_blank_description_is_accepted(self, client):
        user_id = _register(client, "Demo User", "addexpensetest@spendly.com")
        data = {**VALID_EXPENSE, "description": ""}

        response = client.post("/expenses/add", data=data)

        assert response.status_code == 302
        transactions = db_module.get_recent_transactions(user_id)
        assert len(transactions) == 1
        assert transactions[0]["description"] == ""

    def test_expense_always_belongs_to_logged_in_user_not_form_value(self, client):
        """Spec: the inserted expense must always use session["user_id"] --
        never trust a user_id from the form."""
        user_id = _register(client, "Demo User", "addexpensetest@spendly.com")
        data = {**VALID_EXPENSE, "user_id": "99999"}

        client.post("/expenses/add", data=data)

        transactions = db_module.get_recent_transactions(user_id)
        assert len(transactions) == 1, "expense must be attached to the logged-in user"


# ==================================================================== #
# Route-layer tests: POST /expenses/add -- validation failures
# ==================================================================== #

class TestAddExpenseAmountValidation:
    @pytest.mark.parametrize(
        "amount",
        [
            pytest.param("0", id="zero"),
            pytest.param("-10", id="negative"),
            pytest.param("abc", id="non_numeric"),
            pytest.param("", id="missing"),
        ],
    )
    def test_invalid_amount_does_not_create_expense(self, client, amount):
        user_id = _register(client, "Demo User", "addexpensetest@spendly.com")
        data = {**VALID_EXPENSE, "amount": amount}

        response = client.post("/expenses/add", data=data)

        assert response.status_code == 200, "must re-render the form, not redirect"
        assert db_module.get_recent_transactions(user_id) == []

    def test_zero_amount_shows_inline_error(self, client):
        _register(client, "Demo User", "addexpensetest@spendly.com")
        data = {**VALID_EXPENSE, "amount": "0"}

        response = client.post("/expenses/add", data=data)
        body = response.get_data(as_text=True)

        assert "error" in body.lower()


class TestAddExpenseDateValidation:
    @pytest.mark.parametrize(
        "date",
        [
            pytest.param("not-a-date", id="malformed"),
            pytest.param("", id="missing"),
            pytest.param("2026-13-40", id="nonexistent_date"),
        ],
    )
    def test_invalid_date_does_not_create_expense(self, client, date):
        user_id = _register(client, "Demo User", "addexpensetest@spendly.com")
        data = {**VALID_EXPENSE, "date": date}

        response = client.post("/expenses/add", data=data)

        assert response.status_code == 200, "must re-render the form, not redirect"
        assert db_module.get_recent_transactions(user_id) == []


class TestAddExpenseCategoryValidation:
    def test_invalid_category_does_not_create_expense(self, client):
        user_id = _register(client, "Demo User", "addexpensetest@spendly.com")
        data = {**VALID_EXPENSE, "category": "NotACategory"}

        response = client.post("/expenses/add", data=data)

        assert response.status_code == 200, "must re-render the form, not redirect"
        assert db_module.get_recent_transactions(user_id) == []

    def test_missing_category_does_not_create_expense(self, client):
        user_id = _register(client, "Demo User", "addexpensetest@spendly.com")
        data = {**VALID_EXPENSE, "category": ""}

        response = client.post("/expenses/add", data=data)

        assert response.status_code == 200
        assert db_module.get_recent_transactions(user_id) == []


class TestAddExpenseFieldPreservation:
    """Spec: on validation failure, previously entered field values must be
    preserved in the re-rendered form."""

    def test_amount_category_date_description_preserved_on_failure(self, client):
        _register(client, "Demo User", "addexpensetest@spendly.com")
        data = {
            "amount": "-5",
            "category": "Bills",
            "date": "2026-07-15",
            "description": "Preserve me",
        }

        response = client.post("/expenses/add", data=data)
        body = response.get_data(as_text=True)

        assert _input_value(body, "amount") == "-5"
        assert _input_value(body, "date") == "2026-07-15"
        assert _input_value(body, "description") == "Preserve me"

        match = re.search(r'value="Bills"[^>]*>Bills</option>', body)
        assert match is not None and "selected" in match.group(0), (
            "the Bills option should be marked selected"
        )
