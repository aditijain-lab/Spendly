import importlib

import pytest

from database import db as db_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", str(db_path))

    import app as app_module

    importlib.reload(app_module)
    app_module.app.config.update(TESTING=True)

    with app_module.app.test_client() as test_client:
        yield test_client


def test_profile_unauthenticated_redirects_to_login(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_authenticated_seed_user(client):
    client.post(
        "/login", data={"email": "demo@spendly.com", "password": "demo123"}
    )

    response = client.get("/profile")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Demo User" in body
    assert "demo@spendly.com" in body
    assert "₹" in body
    assert "₹3,969.50" in body
    assert "8" in body
    assert "Bills" in body
    for category in [
        "Bills",
        "Shopping",
        "Food",
        "Health",
        "Entertainment",
        "Transport",
        "Other",
    ]:
        assert category in body


def test_profile_new_user_zero_expenses(client):
    client.post(
        "/register",
        data={
            "name": "Fresh User",
            "email": "fresh@example.com",
            "password": "password123",
        },
    )

    response = client.get("/profile")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "₹0.00" in body
