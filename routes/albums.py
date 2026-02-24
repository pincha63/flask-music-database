"""
routes/albums.py — CRUD blueprint for the `albums` table.

Each album belongs to exactly one artist (FK: albums.artist_id → artists.id).
The create/edit forms include a <select> populated with all artists.

Routes
------
GET  /albums/              List all albums (joined with artist name)
GET  /albums/new           Show create form
POST /albums/new           Create a new album
GET  /albums/<id>/edit     Show edit form
POST /albums/<id>/edit     Update an album
POST /albums/<id>/delete   Delete an album (superuser only)
"""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from auth import superuser_required

albums_bp = Blueprint("albums", __name__)


@albums_bp.route("/")
@login_required
def index():
    db = current_app.get_db()
    # JOIN to show the artist name alongside each album
    albums = db.execute("""
        SELECT al.id, al.title, al.release_year, ar.name AS artist_name
        FROM albums al
        JOIN artists ar ON ar.id = al.artist_id
        ORDER BY ar.name, al.release_year
    """).fetchall()
    return render_template("albums/index.html", albums=albums)


@albums_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    db      = current_app.get_db()
    artists = db.execute("SELECT id, name FROM artists ORDER BY name").fetchall()

    if request.method == "POST":
        title        = request.form.get("title", "").strip()
        artist_id    = request.form.get("artist_id", "").strip()
        release_year = request.form.get("release_year", "").strip() or None

        if not title or not artist_id:
            flash("Title and artist are required.", "danger")
            return render_template("albums/form.html", action="Create", album=None, artists=artists)

        try:
            db.execute(
                "INSERT INTO albums (title, artist_id, release_year) VALUES (?, ?, ?)",
                (title, int(artist_id), release_year),
            )
            db.commit()
            flash(f"Album '{title}' created.", "success")
            return redirect(url_for("albums.index"))
        except Exception as e:
            flash(f"Error: {e}", "danger")

    return render_template("albums/form.html", action="Create", album=None, artists=artists)


@albums_bp.route("/<int:album_id>/edit", methods=["GET", "POST"])
@login_required
def edit(album_id):
    db      = current_app.get_db()
    album   = db.execute("SELECT * FROM albums WHERE id = ?", (album_id,)).fetchone()
    artists = db.execute("SELECT id, name FROM artists ORDER BY name").fetchall()

    if album is None:
        flash("Album not found.", "danger")
        return redirect(url_for("albums.index"))

    if request.method == "POST":
        title        = request.form.get("title", "").strip()
        artist_id    = request.form.get("artist_id", "").strip()
        release_year = request.form.get("release_year", "").strip() or None

        if not title or not artist_id:
            flash("Title and artist are required.", "danger")
            return render_template("albums/form.html", action="Update", album=album, artists=artists)

        try:
            db.execute(
                "UPDATE albums SET title = ?, artist_id = ?, release_year = ? WHERE id = ?",
                (title, int(artist_id), release_year, album_id),
            )
            db.commit()
            flash(f"Album '{title}' updated.", "success")
            return redirect(url_for("albums.index"))
        except Exception as e:
            flash(f"Error: {e}", "danger")

    return render_template("albums/form.html", action="Update", album=album, artists=artists)


@albums_bp.route("/<int:album_id>/delete", methods=["POST"])
@login_required
@superuser_required
def delete(album_id):
    db    = current_app.get_db()
    album = db.execute("SELECT title FROM albums WHERE id = ?", (album_id,)).fetchone()

    if album is None:
        flash("Album not found.", "danger")
        return redirect(url_for("albums.index"))

    try:
        db.execute("DELETE FROM albums WHERE id = ?", (album_id,))
        db.commit()
        flash(f"Album '{album['title']}' deleted.", "success")
    except Exception as e:
        flash(f"Cannot delete: {e}", "danger")

    return redirect(url_for("albums.index"))
