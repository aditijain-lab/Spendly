from flask import Flask, render_template, request, redirect, url_for, session

from database.db import get_db, init_db, seed_db, create_user, get_user_by_email, verify_user

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

with app.app_context():
    init_db()
    seed_db()


@app.template_filter("inr")
def format_inr(value):
    return f"₹{value:,.2f}"


# ------------------------------------------------------------------ #
# Hardcoded profile data (Step 4 — real DB queries land in Step 5)    #
# ------------------------------------------------------------------ #

PROFILE_USER = {
    "name": "Demo User",
    "email": "demo@spendly.com",
    "member_since": "January 2026",
    "initials": "DU",
}

PROFILE_STATS = {
    "total_spent": 3969.50,
    "transaction_count": 8,
    "top_category": "Bills",
}

PROFILE_TRANSACTIONS = [
    {"date": "2026-07-07", "description": "Dinner with friends", "category": "Food", "amount": 320.50},
    {"date": "2026-07-06", "description": "Miscellaneous expense", "category": "Other", "amount": 100.00},
    {"date": "2026-07-05", "description": "New shoes", "category": "Shopping", "amount": 899.00},
    {"date": "2026-07-04", "description": "Movie tickets", "category": "Entertainment", "amount": 250.00},
    {"date": "2026-07-03", "description": "Doctor consultation", "category": "Health", "amount": 600.00},
    {"date": "2026-07-02", "description": "Electricity bill", "category": "Bills", "amount": 1200.00},
    {"date": "2026-07-02", "description": "Fuel for car", "category": "Transport", "amount": 150.00},
    {"date": "2026-07-01", "description": "Groceries at supermarket", "category": "Food", "amount": 450.00},
]

PROFILE_CATEGORY_BREAKDOWN = [
    {"name": "Bills", "total": 1200.00, "percent": 30.2, "bar_pct": 30},
    {"name": "Shopping", "total": 899.00, "percent": 22.6, "bar_pct": 25},
    {"name": "Food", "total": 770.50, "percent": 19.4, "bar_pct": 20},
    {"name": "Health", "total": 600.00, "percent": 15.1, "bar_pct": 15},
    {"name": "Entertainment", "total": 250.00, "percent": 6.3, "bar_pct": 5},
    {"name": "Transport", "total": 150.00, "percent": 3.8, "bar_pct": 5},
    {"name": "Other", "total": 100.00, "percent": 2.5, "bar_pct": 5},
]


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not name or not email or not password:
        return render_template(
            "register.html", error="All fields are required.", name=name, email=email
        )

    if get_user_by_email(email) is not None:
        return render_template(
            "register.html",
            error="An account with that email already exists.",
            name=name,
            email=email,
        )

    user_id = create_user(name, email, password)
    session["user_id"] = user_id
    session["user_name"] = name
    return redirect(url_for("profile"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template(
            "login.html", error="Email and password are required.", email=email
        )

    user = verify_user(email, password)
    if user is None:
        return render_template(
            "login.html", error="Invalid email or password.", email=email
        )

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template(
        "profile.html",
        user=PROFILE_USER,
        stats=PROFILE_STATS,
        transactions=PROFILE_TRANSACTIONS,
        categories=PROFILE_CATEGORY_BREAKDOWN,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
