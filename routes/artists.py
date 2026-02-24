"""
routes/artists.py — CRUD blueprint for the `artists` table.

Routes
------
GET  /artists/              List all artists
GET  /artists/new           Show create form
POST /artists/new           Create a new artist
GET  /artists/<id>/edit     Show edit form
POST /artists/<id>/edit     Update an artist
POST /artists/<id>/delete   Delete an artist (superuser only)
"""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from auth import superuser_required

artists_bp = Blueprint("artists", __name__)


@artists_bp.route("/")
@login_required
def index():
    """Return a list of all artists ordered by name."""
    db = current_app.get_db()
    artists = db.execute("SELECT * FROM artists ORDER BY name").fetchall()
    return render_template("artists/index.html", artists=artists)


@artists_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    """Show the create form (GET) or insert a new artist (POST)."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        bio  = request.form.get("bio",  "").strip() or None

        if not name:
            flash("Artist name is required.", "danger")
            return render_template("artists/form.html", action="Create", artist=None)

        db = current_app.get_db()
        try:
            db.execute("INSERT INTO artists (name, bio) VALUES (?, ?)", (name, bio))
            db.commit()
            flash(f"Artist '{name}' created.", "success")
            return redirect(url_for("artists.index"))
        except Exception as e:
            flash(f"Error: {e}", "danger")

    return render_template("artists/form.html", action="Create", artist=None)


@artists_bp.route("/<int:artist_id>/edit", methods=["GET", "POST"])
@login_required
def edit(artist_id):
    """Show the edit form (GET) or update an existing artist (POST)."""
    db     = current_app.get_db()
    artist = db.execute("SELECT * FROM artists WHERE id = ?", (artist_id,)).fetchone()

    if artist is None:
        flash("Artist not found.", "danger")
        return redirect(url_for("artists.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        bio  = request.form.get("bio",  "").strip() or None

        if not name:
            flash("Artist name is required.", "danger")
            return render_template("artists/form.html", action="Update", artist=artist)

        try:
            db.execute(
                "UPDATE artists SET name = ?, bio = ? WHERE id = ?",
                (name, bio, artist_id),
            )
            db.commit()
            flash(f"Artist '{name}' updated.", "success")
            return redirect(url_for("artists.index"))
        except Exception as e:
            flash(f"Error: {e}", "danger")

    return render_template("artists/form.html", action="Update", artist=artist)


@artists_bp.route("/<int:artist_id>/delete", methods=["POST"])
@login_required
@superuser_required
def delete(artist_id):
    """
    Delete an artist.

    Protected by @superuser_required — only 'sandro63' can reach this route.
    The foreign-key constraint on `albums.artist_id` will raise an error if
    the artist still has albums; that error is caught and shown as a flash msg.
    """
    db     = current_app.get_db()
    artist = db.execute("SELECT name FROM artists WHERE id = ?", (artist_id,)).fetchone()

    if artist is None:
        flash("Artist not found.", "danger")
        return redirect(url_for("artists.index"))

    try:
        db.execute("DELETE FROM artists WHERE id = ?", (artist_id,))
        db.commit()
        flash(f"Artist '{artist['name']}' deleted.", "success")
    except Exception as e:
        flash(f"Cannot delete: {e}", "danger")

    return redirect(url_for("artists.index"))
