from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, abort

from database.db import (
    get_db,
    init_db,
    seed_db,
    create_user,
    get_user_by_email,
    verify_user,
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

with app.app_context():
    init_db()
    seed_db()


@app.template_filter("inr")
def format_inr(value):
    return f"₹{value:,.2f}"


def _parse_date_filter(raw_start, raw_end):
    """Return (start_date, end_date) as 'YYYY-MM-DD' strings, or (None, None) if the
    filter is missing, incomplete, malformed, or start > end."""
    if not raw_start or not raw_end:
        return None, None
    try:
        start_dt = datetime.strptime(raw_start, "%Y-%m-%d")
        end_dt = datetime.strptime(raw_end, "%Y-%m-%d")
    except ValueError:
        return None, None
    if start_dt > end_dt:
        return None, None
    return raw_start, raw_end


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


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user = get_user_by_id(user_id)
    if user is None:
        abort(404)

    start_date, end_date = _parse_date_filter(
        request.args.get("start_date"), request.args.get("end_date")
    )

    return render_template(
        "profile.html",
        user=user,
        stats=get_summary_stats(user_id, start_date, end_date),
        transactions=get_recent_transactions(user_id, start_date=start_date, end_date=end_date),
        categories=get_category_breakdown(user_id, start_date, end_date),
        start_date=start_date,
        end_date=end_date,
        filter_active=bool(start_date and end_date),
    )


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

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
