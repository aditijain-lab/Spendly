# Spec: Registration

## Overview

This step implements user registration for Spendly. Currently `GET /register` only renders a static form with no backend logic — submitting it does nothing. This step wires the form up to create a real user record in the `users` table, with validation and password hashing, and establishes a logged-in session so the user lands in the app immediately after signing up. Registration is the first step in the authentication flow and is a prerequisite for login, logout, and profile.

## Depends on

- Step 01 — Database setup (`users` table, `get_db()`, `init_db()`, `seed_db()`) — complete

## Routes

- `POST /register` — create a new user account, hash the password, start a session, redirect to a logged-in landing point — public
- `GET /register` — already implemented (renders the form) — no change to this handler beyond what's needed to redisplay errors

No other new routes.

## Database changes

No database changes. The `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) already supports registration as defined in `database/db.py`. This step only adds a query function to insert a new row and one to check for an existing email — no schema changes.

## Templates

**Create:** None.

**Modify:**
- `templates/register.html` — display validation/duplicate-email errors returned by `POST /register` (the template already has an `{% if error %}` block wired up; ensure field values are re-populated on error so the user doesn't have to retype everything)

## Files to change

- `app.py` — add `POST` handling to the `/register` route (or add a dedicated view function), validate input, call the new `db.py` helper to create the user, start the session, redirect on success
- `database/db.py` — add `create_user(name, email, password)` (hashes password, inserts row, returns new user id) and `get_user_by_email(email)` (used for duplicate-email + future login checks)
- `templates/register.html` — re-populate `name`/`email` values on redisplay after a validation error

## Files to create

None.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterized queries only — no f-strings in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic belongs only in `database/db.py`, never inline in `app.py`
- Validate on the server even though the form has `required`/`type=email` attributes client-side (never trust client-only validation)
- Duplicate email must be rejected with a user-facing error, not a raw exception (SQLite `UNIQUE` constraint on `email` backs this up, but check first and give a clean message)
- Use `abort()` for HTTP errors, not bare `return "error string"`
- Do not touch any other stub route (`/logout`, `/profile`, `/expenses/*`) — those stay stubs until their own step

## Definition of done

- [ ] Submitting the register form with a new name/email/password creates a row in `users` with a hashed (not plaintext) password
- [ ] Submitting with an email that already exists (e.g. `demo@spendly.com`) redisplays the form with an error and does not create a duplicate row
- [ ] Submitting with a missing field (blank name/email/password) redisplays the form with an error instead of raising a server error
- [ ] After successful registration, the user is redirected away from `/register` (not shown the form again)
- [ ] Inspecting `expense_tracker.db` after registering shows the new user's `password_hash` is a werkzeug hash, not the raw password
- [ ] App still starts cleanly with `python app.py` on port 5001
- [ ] All other stub routes (`/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`) still return their original stub responses, unchanged
