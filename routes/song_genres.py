"""
routes/song_genres.py — Manage the song_genres many-to-many junction table.

A song can belong to multiple genres.

Routes
------
GET  /song-genres/        List all associations + show add form
POST /song-genres/add     Create a new association
POST /song-genres/remove  Remove an association (superuser only)
"""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from auth import superuser_required

song_genres_bp = Blueprint("song_genres", __name__)


@song_genres_bp.route("/")
@login_required
def index():
    db = current_app.get_db()

    rows = db.execute("""
        SELECT s.id  AS song_id,  s.title  AS song_title,
               g.id  AS genre_id, g.name   AS genre_name
        FROM song_genres sg
        JOIN songs  s ON s.id = sg.song_id
        JOIN genres g ON g.id = sg.genre_id
        ORDER BY s.title, g.name
    """).fetchall()

    songs  = db.execute("SELECT id, title FROM songs  ORDER BY title").fetchall()
    genres = db.execute("SELECT id, name  FROM genres ORDER BY name").fetchall()

    return render_template("song_genres/index.html", rows=rows, songs=songs, genres=genres)


@song_genres_bp.route("/add", methods=["POST"])
@login_required
def add():
    song_id  = request.form.get("song_id",  "").strip()
    genre_id = request.form.get("genre_id", "").strip()

    if not song_id or not genre_id:
        flash("Both song and genre are required.", "danger")
        return redirect(url_for("song_genres.index"))

    db = current_app.get_db()
    try:
        db.execute(
            "INSERT INTO song_genres (song_id, genre_id) VALUES (?, ?)",
            (int(song_id), int(genre_id)),
        )
        db.commit()
        flash("Association added.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")

    return redirect(url_for("song_genres.index"))


@song_genres_bp.route("/remove", methods=["POST"])
@login_required
@superuser_required
def remove():
    song_id  = request.form.get("song_id",  "").strip()
    genre_id = request.form.get("genre_id", "").strip()

    db = current_app.get_db()
    try:
        db.execute(
            "DELETE FROM song_genres WHERE song_id = ? AND genre_id = ?",
            (int(song_id), int(genre_id)),
        )
        db.commit()
        flash("Association removed.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")

    return redirect(url_for("song_genres.index"))
