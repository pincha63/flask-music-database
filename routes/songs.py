"""
routes/songs.py — CRUD blueprint for the `songs` table.

Duration is stored in the database as an integer (seconds) but displayed
and accepted in m:ss format for usability.

Routes
------
GET  /songs/              List all songs
GET  /songs/new           Show create form
POST /songs/new           Create a new song
GET  /songs/<id>/edit     Show edit form
POST /songs/<id>/edit     Update a song
POST /songs/<id>/delete   Delete a song (superuser only)
"""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from auth import superuser_required

songs_bp = Blueprint("songs", __name__)


# ── Duration helpers ──────────────────────────────────────────────────────────

def seconds_to_mmss(seconds: int) -> str:
    """Convert an integer number of seconds to a 'm:ss' string."""
    if seconds is None:
        return ""
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def mmss_to_seconds(mmss: str) -> int | None:
    """
    Parse a 'm:ss' or plain integer string to seconds.
    Returns None if the input is empty or unparseable.
    """
    if not mmss:
        return None
    mmss = mmss.strip()
    if ":" in mmss:
        parts = mmss.split(":", 1)
        try:
            return int(parts[0]) * 60 + int(parts[1])
        except ValueError:
            return None
    try:
        return int(mmss)
    except ValueError:
        return None


# ── Routes ────────────────────────────────────────────────────────────────────

@songs_bp.route("/")
@login_required
def index():
    db    = current_app.get_db()
    songs = db.execute("SELECT * FROM songs ORDER BY title").fetchall()
    # Convert duration to display format for the template
    songs_display = [
        {**dict(s), "duration_display": seconds_to_mmss(s["duration"])}
        for s in songs
    ]
    return render_template("songs/index.html", songs=songs_display)


@songs_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        title    = request.form.get("title", "").strip()
        duration = mmss_to_seconds(request.form.get("duration", ""))

        if not title:
            flash("Song title is required.", "danger")
            return render_template("songs/form.html", action="Create", song=None)

        db = current_app.get_db()
        try:
            db.execute("INSERT INTO songs (title, duration) VALUES (?, ?)", (title, duration))
            db.commit()
            flash(f"Song '{title}' created.", "success")
            return redirect(url_for("songs.index"))
        except Exception as e:
            flash(f"Error: {e}", "danger")

    return render_template("songs/form.html", action="Create", song=None)


@songs_bp.route("/<int:song_id>/edit", methods=["GET", "POST"])
@login_required
def edit(song_id):
    db   = current_app.get_db()
    song = db.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()

    if song is None:
        flash("Song not found.", "danger")
        return redirect(url_for("songs.index"))

    if request.method == "POST":
        title    = request.form.get("title", "").strip()
        duration = mmss_to_seconds(request.form.get("duration", ""))

        if not title:
            flash("Song title is required.", "danger")
            return render_template("songs/form.html", action="Update",
                                   song={**dict(song), "duration_display": seconds_to_mmss(song["duration"])})

        try:
            db.execute(
                "UPDATE songs SET title = ?, duration = ? WHERE id = ?",
                (title, duration, song_id),
            )
            db.commit()
            flash(f"Song '{title}' updated.", "success")
            return redirect(url_for("songs.index"))
        except Exception as e:
            flash(f"Error: {e}", "danger")

    song_display = {**dict(song), "duration_display": seconds_to_mmss(song["duration"])}
    return render_template("songs/form.html", action="Update", song=song_display)


@songs_bp.route("/<int:song_id>/delete", methods=["POST"])
@login_required
@superuser_required
def delete(song_id):
    db   = current_app.get_db()
    song = db.execute("SELECT title FROM songs WHERE id = ?", (song_id,)).fetchone()

    if song is None:
        flash("Song not found.", "danger")
        return redirect(url_for("songs.index"))

    try:
        db.execute("DELETE FROM songs WHERE id = ?", (song_id,))
        db.commit()
        flash(f"Song '{song['title']}' deleted.", "success")
    except Exception as e:
        flash(f"Cannot delete: {e}", "danger")

    return redirect(url_for("songs.index"))
