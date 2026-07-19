Spec: Add Expense

Overview
Step 7 implements the "Add Expense" form so logged-in users can create new expense records instead of relying only on seeded data. GET /expenses/add renders a form (amount, category, date, description); POST /expenses/add validates the input, inserts the row for the current user, and redirects to the profile page where the new expense immediately shows up in Recent Transactions, Summary Stats, and Category Breakdown.

Depends on
Step 1: Database setup (expenses table and get_db() exist)
Step 2: Registration (users are stored in the database)
Step 3: Login / Logout (session["user_id"] is set on login)
Step 5: Backend connection for profile page (profile() reads live data via database/db.py)

Routes
GET /expenses/add — modified (was stub) — logged-in — renders the add-expense form; redirects to /login if not logged in
POST /expenses/add — new — logged-in — validates form fields, inserts the expense for session["user_id"], redirects to /profile on success; re-renders the form with an error message and the submitted values on validation failure

Database changes
No database changes. The existing `expenses` table (id, user_id, amount, category, date, description, created_at) already supports inserting new rows; database/db.py needs a new `create_expense(user_id, amount, category, date, description)` helper using a parameterised INSERT.

Templates
Create: templates/add_expense.html — form with amount (number input), category (select, options: Food, Transport, Bills, Health, Entertainment, Shopping, Other), date (date input, defaults to today), description (text input, optional), submit button, and an error message area; extends base.html
Files to change
app.py — add_expense() gains POST handling: read/validate form fields, call create_expense(), redirect to profile() on success or re-render add_expense.html with error + submitted values on failure
database/db.py — add create_expense(user_id, amount, category, date, description) that inserts a parameterised row into expenses and returns the new id

Files to create
templates/add_expense.html
static/css/add_expense.css — form styling using existing CSS variables

New dependencies
No new dependencies.

Rules for implementation
No SQLAlchemy or ORMs — raw sqlite3 only via get_db()
Parameterised queries only — never string-format values into SQL
Foreign keys PRAGMA must be enabled on every connection (already done in get_db())
Use CSS variables — never hardcode hex values
All templates extend base.html
No inline styles
Currency must always display as ₹ — never £ or $
Never use raw string returns for this route now that it's implemented — always render a template
amount must be a positive number (> 0); reject zero, negative, non-numeric, or missing values with an inline error, no 500
category must be one of the fixed allowed values; reject anything else with an inline error
date must be a valid YYYY-MM-DD date; reject malformed or missing dates with an inline error
description is optional and may be empty
The inserted expense must always use session["user_id"] as user_id — never trust a user_id from the form
On validation failure, previously entered field values must be preserved in the re-rendered form
Definition of done
 Visiting /expenses/add while logged out redirects to /login
 Visiting /expenses/add while logged in shows the empty add-expense form with today's date pre-filled
 Submitting a valid amount, category, date, and description creates a new expense and redirects to /profile
 The new expense appears in Recent Transactions, updates Summary Stats (Total Spent, Transactions, Top Category), and updates Category Breakdown on the profile page
 Submitting a zero, negative, or non-numeric amount re-shows the form with an inline error and no expense is created
 Submitting an invalid or missing date re-shows the form with an inline error and no expense is created
 Submitting an invalid category re-shows the form with an inline error and no expense is created
 Submitting with description left blank succeeds and the expense is created with an empty description
 After a validation failure, previously entered amount/category/date/description values remain in the form fields
