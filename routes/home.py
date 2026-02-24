"""
routes/home.py — Dashboard blueprint.

Shows a summary card for each entity with a live record count fetched
from the database.  Requires authentication.
"""

from flask import Blueprint, current_app, render_template
from flask_login import login_required

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
@login_required
def index():
    """Render the dashboard with record counts for all seven tables."""
    db = current_app.get_db()

    # Fetch counts for every table in one round-trip each
    counts = {
        "artists":     db.execute("SELECT COUNT(*) FROM artists").fetchone()[0],
        "albums":      db.execute("SELECT COUNT(*) FROM albums").fetchone()[0],
        "songs":       db.execute("SELECT COUNT(*) FROM songs").fetchone()[0],
        "genres":      db.execute("SELECT COUNT(*) FROM genres").fetchone()[0],
        "album_songs": db.execute("SELECT COUNT(*) FROM album_songs").fetchone()[0],
        "song_genres": db.execute("SELECT COUNT(*) FROM song_genres").fetchone()[0],
        "album_genres":db.execute("SELECT COUNT(*) FROM album_genres").fetchone()[0],
    }

    return render_template("home.html", counts=counts)
