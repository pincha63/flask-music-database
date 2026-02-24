"""
auth.py — Authentication module for the Music Database Manager.

Provides:
  - A simple in-memory user store (no database table needed for this demo).
  - The Flask-Login User class.
  - Login / logout routes (registered as the 'auth' Blueprint).
  - The @superuser_required decorator that restricts delete operations
    to the user whose username is 'sandro63'.

In a production system the USERS dict would be replaced by a database
table with bcrypt-hashed passwords.
"""

from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import UserMixin, current_user, login_required, login_user, logout_user

# ── Hard-coded user store ─────────────────────────────────────────────────────
# Keys are usernames; values are plain-text passwords (demo only).
# The superuser is identified by the username 'sandro63'.
USERS = {
    "sandro63": "sandro63",   # superuser — has delete privilege
    "guest":    "guest",      # regular user — create & update only
}

SUPERUSER = "sandro63"


# ── Flask-Login User class ────────────────────────────────────────────────────
class User(UserMixin):
    """
    Minimal user object required by Flask-Login.

    Flask-Login stores the user's `id` (= username) in the signed session
    cookie and calls load_user() on every request to reconstruct this object.
    """

    def __init__(self, username: str):
        self.id = username          # Flask-Login uses `id` as the session key

    @property
    def is_superuser(self) -> bool:
        """Return True only for the designated superuser account."""
        return self.id == SUPERUSER


def load_user(user_id: str):
    """
    Flask-Login user loader callback.

    Called on every request with the user_id stored in the session cookie.
    Returns a User instance if the id is valid, or None to force logout.
    """
    if user_id in USERS:
        return User(user_id)
    return None


# ── Superuser decorator ───────────────────────────────────────────────────────
def superuser_required(f):
    """
    Route decorator that restricts access to the superuser ('sandro63').

    Must be applied AFTER @login_required so that unauthenticated users are
    redirected to the login page before this check runs.

    Usage:
        @bp.route("/<int:id>/delete", methods=["POST"])
        @login_required
        @superuser_required
        def delete(id):
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_superuser:
            flash("Only the superuser (sandro63) can delete records.", "danger")
            return redirect(request.referrer or url_for("home.index"))
        return f(*args, **kwargs)
    return decorated


# ── Auth Blueprint ────────────────────────────────────────────────────────────
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Display the login form (GET) or process credentials (POST)."""
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Validate credentials against the in-memory store
        if username in USERS and USERS[username] == password:
            user = User(username)
            login_user(user)
            # Honour the 'next' parameter set by @login_required redirects
            next_page = request.args.get("next") or url_for("home.index")
            return redirect(next_page)

        flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Log the current user out and redirect to the login page."""
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
