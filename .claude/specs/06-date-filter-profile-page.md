Spec: Date Filter For Profile Page

Overview
Step 6 adds a date-range filter to the profile page so users can narrow the transaction history, summary stats, and category breakdown to a specific window instead of always seeing all-time data. The filter is expressed as `start_date` and `end_date` query-string parameters on GET /profile, defaulting to all-time data when absent, so the page keeps working exactly as it does today for users who don't filter.

Depends on
Step 1: Database setup (tables and get_db() exist)
Step 2: Registration (users are stored in the database)
Step 3: Login / Logout (session["user_id"] is set on login)
Step 5: Backend connection for profile page (profile() reads live data via database/db.py)

Routes
GET /profile — modified — logged-in — now accepts optional `start_date` and `end_date` query-string parameters (format YYYY-MM-DD) and filters stats, transactions, and category breakdown to that range. No new routes.

Database changes
No database changes. The `expenses.date` column (TEXT, stored as YYYY-MM-DD) already supports range filtering with standard SQL comparison operators.

Templates
Modify: templates/profile.html — add a date filter form (two date inputs + submit) above the Transaction History section, submitting via GET to preserve the filtered URL; show a "Clear filter" link when a filter is active.
Files to change
app.py — profile() reads start_date/end_date from request.args and passes them to the db helpers and back to the template for pre-filling the form
database/db.py — get_summary_stats, get_recent_transactions, get_category_breakdown gain optional start_date/end_date parameters that add a parameterised `AND date BETWEEN ? AND ?` clause when both are provided
templates/profile.html — add filter form, pre-fill selected dates, show active-filter state
static/css/profile.css — style the new filter form using existing CSS variables

Files to create
None.

New dependencies
No new dependencies.

Rules for implementation
No SQLAlchemy or ORMs — raw sqlite3 only via get_db()
Parameterised queries only — never string-format values into SQL, including the date range
Foreign keys PRAGMA must be enabled on every connection (already done in get_db())
Use CSS variables — never hardcode hex values
All templates extend base.html
No inline styles
Currency must always display as ₹ — never £ or $
If start_date is after end_date, ignore the filter and treat the request as unfiltered (do not error)
If only one of start_date/end_date is supplied, ignore the filter and treat the request as unfiltered
Invalid date formats must be ignored, not raise a 500 — fall back to unfiltered
Filtering must never leak another user's expenses — the existing `WHERE user_id = ?` clause stays in every query
Definition of done
 Visiting /profile with no query params shows the same all-time data as before this change
 Submitting a valid start_date and end_date filters the Transaction History table to only rows within that range (inclusive)
 Summary stats (Total Spent, Transactions, Top Category) update to reflect only the filtered range
 Category Breakdown updates to reflect only the filtered range and percentages still sum to 100%
 The date inputs remain pre-filled with the submitted values after the page reloads
 A "Clear filter" control is visible when a filter is active and returns the user to /profile with no query params
 Submitting only one date, or start_date after end_date, shows all-time data without an error page
 Filtering to a range with no matching expenses shows ₹0.00 total, 0 transactions, an empty transaction table, and an empty category breakdown — no errors
