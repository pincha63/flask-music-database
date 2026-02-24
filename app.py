"""
app.py — Flask application factory for the Music Database Manager.

This is the sole Python entry point.  It:
  - Creates and configures the Flask application instance.
  - Initialises Flask-Login for session-based authentication.
  - Opens (and seeds) the SQLite database on first request.
  - Registers all Blueprints (one per database entity).
  - Provides the get_db() / close_db() helpers used by every route.

Usage
-----
Development:
    python3 app.py

Production (Gunicorn):
    gunicorn "app:create_app()" --bind 0.0.0.0:8000 --workers 4
"""

import os
import sqlite3

from flask import Flask, g
from flask_login import LoginManager

# ── Blueprint imports ─────────────────────────────────────────────────────────
from routes.home        import home_bp
from routes.artists     import artists_bp
from routes.albums      import albums_bp
from routes.songs       import songs_bp
from routes.genres      import genres_bp
from routes.album_songs import album_songs_bp
from routes.song_genres import song_genres_bp
from routes.album_genres import album_genres_bp
from auth               import auth_bp, load_user


def create_app():
    """Application factory — create and return a configured Flask instance."""

    app = Flask(__name__, instance_relative_config=True)

    # ── Secret key (override via SECRET_KEY env var in production) ────────────
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")

    # ── Database path inside the instance/ folder ─────────────────────────────
    app.config["DATABASE"] = os.path.join(app.instance_path, "music.db")

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # ── Flask-Login setup ─────────────────────────────────────────────────────
    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"          # redirect unauthenticated users here
    login_manager.login_message = "Please sign in to access this page."
    login_manager.login_message_category = "warning"
    login_manager.user_loader(load_user)

    # ── Database helpers ──────────────────────────────────────────────────────
    def get_db():
        """
        Return the SQLite connection for the current request.

        The connection is stored on Flask's application-context object `g`
        so that the same connection is reused for all queries within a single
        request, and closed automatically when the request ends.
        """
        if "db" not in g:
            g.db = sqlite3.connect(
                app.config["DATABASE"],
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            g.db.row_factory = sqlite3.Row          # rows behave like dicts
            # SQLite does NOT enforce foreign keys by default — enable it here
            # so every connection respects referential integrity constraints.
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

    # Attach get_db to the app so blueprints can call current_app.get_db()
    # without importing from app.py (which would create a circular import).
    app.get_db = get_db

    @app.teardown_appcontext
    def close_db(exception=None):
        """Close the database connection at the end of every request."""
        db = g.pop("db", None)
        if db is not None:
            db.close()

    # ── Initialise / seed the database on first use ───────────────────────────
    _init_db(app)

    # ── Register Blueprints ───────────────────────────────────────────────────
    app.register_blueprint(auth_bp,        url_prefix="/auth")
    app.register_blueprint(home_bp,        url_prefix="/")
    app.register_blueprint(artists_bp,     url_prefix="/artists")
    app.register_blueprint(albums_bp,      url_prefix="/albums")
    app.register_blueprint(songs_bp,       url_prefix="/songs")
    app.register_blueprint(genres_bp,      url_prefix="/genres")
    app.register_blueprint(album_songs_bp, url_prefix="/album-songs")
    app.register_blueprint(song_genres_bp, url_prefix="/song-genres")
    app.register_blueprint(album_genres_bp,url_prefix="/album-genres")

    return app


def _init_db(app):
    """
    Create and seed the database if it does not already exist.

    The SQL script (music_database.sql) contains both the DDL (CREATE TABLE
    statements with foreign-key constraints) and the seed INSERT statements.
    Running it is idempotent because every CREATE TABLE uses IF NOT EXISTS.
    """
    db_path  = app.config["DATABASE"]
    sql_path = os.path.join(os.path.dirname(__file__), "music_database.sql")

    if not os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            with open(sql_path, "r") as f:
                conn.executescript(f.read())
        print(f"[db] Initialised database at {db_path}")


# ── Development server entry point ────────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
