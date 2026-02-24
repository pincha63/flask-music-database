"""
routes/album_genres.py — Manage the album_genres many-to-many junction table.

An album can belong to zero or more genres.

Routes
------
GET  /album-genres/        List all associations + show add form
POST /album-genres/add     Create a new association
POST /album-genres/remove  Remove an association (superuser only)
"""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from auth import superuser_required

album_genres_bp = Blueprint("album_genres", __name__)


@album_genres_bp.route("/")
@login_required
def index():
    db = current_app.get_db()

    rows = db.execute("""
        SELECT al.id AS album_id, al.title AS album_title,
               g.id  AS genre_id, g.name   AS genre_name
        FROM album_genres ag
        JOIN albums al ON al.id = ag.album_id
        JOIN genres g  ON g.id  = ag.genre_id
        ORDER BY al.title, g.name
    """).fetchall()

    albums = db.execute("SELECT id, title FROM albums ORDER BY title").fetchall()
    genres = db.execute("SELECT id, name  FROM genres ORDER BY name").fetchall()

    return render_template("album_genres/index.html", rows=rows, albums=albums, genres=genres)


@album_genres_bp.route("/add", methods=["POST"])
@login_required
def add():
    album_id = request.form.get("album_id", "").strip()
    genre_id = request.form.get("genre_id", "").strip()

    if not album_id or not genre_id:
        flash("Both album and genre are required.", "danger")
        return redirect(url_for("album_genres.index"))

    db = current_app.get_db()
    try:
        db.execute(
            "INSERT INTO album_genres (album_id, genre_id) VALUES (?, ?)",
            (int(album_id), int(genre_id)),
        )
        db.commit()
        flash("Association added.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")

    return redirect(url_for("album_genres.index"))


@album_genres_bp.route("/remove", methods=["POST"])
@login_required
@superuser_required
def remove():
    album_id = request.form.get("album_id", "").strip()
    genre_id = request.form.get("genre_id", "").strip()

    db = current_app.get_db()
    try:
        db.execute(
            "DELETE FROM album_genres WHERE album_id = ? AND genre_id = ?",
            (int(album_id), int(genre_id)),
        )
        db.commit()
        flash("Association removed.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")

    return redirect(url_for("album_genres.index"))
