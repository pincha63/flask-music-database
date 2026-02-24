"""
routes/album_songs.py — Manage the album_songs many-to-many junction table.

A song can appear on multiple albums; an album can contain multiple songs.
This blueprint lets users add and remove those associations.

Routes
------
GET  /album-songs/        List all associations + show add form
POST /album-songs/add     Create a new association
POST /album-songs/remove  Remove an association (superuser only)
"""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from auth import superuser_required

album_songs_bp = Blueprint("album_songs", __name__)


@album_songs_bp.route("/")
@login_required
def index():
    db = current_app.get_db()

    # All existing associations with human-readable names
    rows = db.execute("""
        SELECT al.id AS album_id, al.title AS album_title,
               s.id  AS song_id,  s.title  AS song_title
        FROM album_songs als
        JOIN albums al ON al.id = als.album_id
        JOIN songs  s  ON s.id  = als.song_id
        ORDER BY al.title, s.title
    """).fetchall()

    albums = db.execute("SELECT id, title FROM albums ORDER BY title").fetchall()
    songs  = db.execute("SELECT id, title FROM songs  ORDER BY title").fetchall()

    return render_template("album_songs/index.html", rows=rows, albums=albums, songs=songs)


@album_songs_bp.route("/add", methods=["POST"])
@login_required
def add():
    album_id = request.form.get("album_id", "").strip()
    song_id  = request.form.get("song_id",  "").strip()

    if not album_id or not song_id:
        flash("Both album and song are required.", "danger")
        return redirect(url_for("album_songs.index"))

    db = current_app.get_db()
    try:
        db.execute(
            "INSERT INTO album_songs (album_id, song_id) VALUES (?, ?)",
            (int(album_id), int(song_id)),
        )
        db.commit()
        flash("Association added.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")

    return redirect(url_for("album_songs.index"))


@album_songs_bp.route("/remove", methods=["POST"])
@login_required
@superuser_required
def remove():
    album_id = request.form.get("album_id", "").strip()
    song_id  = request.form.get("song_id",  "").strip()

    db = current_app.get_db()
    try:
        db.execute(
            "DELETE FROM album_songs WHERE album_id = ? AND song_id = ?",
            (int(album_id), int(song_id)),
        )
        db.commit()
        flash("Association removed.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")

    return redirect(url_for("album_songs.index"))
