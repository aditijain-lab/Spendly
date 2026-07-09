# Spec: Login and Logout

## Overview

This step implements authentication for existing users. Currently `GET /login` only renders a static form with a hardcoded `action="/login"` and no backend logic — submitting it does nothing. `GET /logout` is a stub that returns a raw string. This step wires the login form to verify credentials against the `users` table and start a session, and implements logout to clear the session and return the user to a logged-out state. Login and logout complete the authentication flow started in Step 02 (Registration) and are prerequisites for Step 04 (Profile) and all expense routes.

## Depends on

- Step 01 — Database setup (`users` table, `get_db()`, `init_db()`, `seed_db()`) — complete
- Step 02 — Registration (`create_user()`, `get_user_by_email()`, session pattern of `session["user_id"]` / `session["user_name"]`) — complete

## Routes

- `POST /login` — verify email + password against the `users` table, start a session, redirect to a logged-in landing point — public
- `GET /login` — already implemented (renders the form) — modify only to redisplay errors, same pattern as `/register`
- `GET /logout` — clear the session and redirect to the landing page — logged-in (safe to call when logged out too; it just clears an empty session)

No other new routes. `/profile` stays a stub (Step 04).

## Database changes

No database changes. The `users` table already supports login via the existing `email` and `password_hash` columns. This step adds one new query function to `database/db.py` for password verification — no schema changes.

## Templates

**Create:** None.

**Modify:**
- `templates/login.html` — change hardcoded `action="/login"` to `action="{{ url_for('login') }}"` (never hardcode URLs); display a login error (invalid email/password) the same way `register.html` displays its error; re-populate the `email` field value on redisplay after an error

## Files to change

- `app.py` — add `POST` handling to the `/login` route: read form fields, validate presence, look up the user, verify the password hash, start the session (`session["user_id"]`, `session["user_name"]`) on success or redisplay the form with an error on failure; implement `/logout` to clear the session (`session.clear()`) and redirect to `landing`
- `database/db.py` — add `verify_user(email, password)` (looks up the user by email, checks the password with `werkzeug.security.check_password_hash`, returns the user row on success or `None` on failure) — do not duplicate the existing `get_user_by_email()`, reuse it inside `verify_user()`
- `templates/login.html` — fix hardcoded form action, add error display, re-populate `email` on redisplay

## Files to create

None.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterized queries only — no f-strings in SQL
- Passwords verified with `werkzeug.security.check_password_hash` (never compare plaintext passwords)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic belongs only in `database/db.py`, never inline in `app.py`
- Validate on the server even though the form has `required`/`type=email` attributes client-side (never trust client-only validation)
- Invalid credentials must show one generic error (e.g. "Invalid email or password") — never reveal whether the email exists or the password was wrong, that's a security leak
- Use `abort()` for HTTP errors, not bare `return "error string"`
- Do not touch any other stub route (`/profile`, `/expenses/*`) — those stay stubs until their own step
- `/logout` must render nothing and return no raw string — it only clears session state and redirects

## Definition of done

- [ ] Logging in with the seeded demo account (`demo@spendly.com` / `demo123`) starts a session and redirects away from `/login`
- [ ] Logging in with a correct email but wrong password redisplays the form with a generic invalid-credentials error, not a server error
- [ ] Logging in with an email that doesn't exist redisplays the form with the same generic invalid-credentials error (no leak of which part was wrong)
- [ ] Logging in with a missing field (blank email/password) redisplays the form with an error instead of raising a server error
- [ ] Visiting `/logout` after logging in clears the session and redirects to the landing page
- [ ] After `/logout`, the nav bar shows the logged-out state (Sign in / Get started links) again
- [ ] `templates/login.html` no longer hardcodes `action="/login"` — it uses `url_for('login')`
- [ ] App still starts cleanly with `python app.py` on port 5001
- [ ] All other stub routes (`/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`) still return their original stub responses, unchanged
