"""
routes/genres.py — CRUD blueprint for the `genres` table.

Routes
------
GET  /genres/              List all genres
GET  /genres/new           Show create form
POST /genres/new           Create a new genre
GET  /genres/<id>/edit     Show edit form
POST /genres/<id>/edit     Update a genre
POST /genres/<id>/delete   Delete a genre (superuser only)
"""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from auth import superuser_required

genres_bp = Blueprint("genres", __name__)


@genres_bp.route("/")
@login_required
def index():
    db = current_app.get_db()
    genres = db.execute("SELECT * FROM genres ORDER BY name").fetchall()
    return render_template("genres/index.html", genres=genres)


@genres_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Genre name is required.", "danger")
            return render_template("genres/form.html", action="Create", genre=None)

        db = current_app.get_db()
        try:
            db.execute("INSERT INTO genres (name) VALUES (?)", (name,))
            db.commit()
            flash(f"Genre '{name}' created.", "success")
            return redirect(url_for("genres.index"))
        except Exception as e:
            flash(f"Error: {e}", "danger")

    return render_template("genres/form.html", action="Create", genre=None)


@genres_bp.route("/<int:genre_id>/edit", methods=["GET", "POST"])
@login_required
def edit(genre_id):
    db    = current_app.get_db()
    genre = db.execute("SELECT * FROM genres WHERE id = ?", (genre_id,)).fetchone()

    if genre is None:
        flash("Genre not found.", "danger")
        return redirect(url_for("genres.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Genre name is required.", "danger")
            return render_template("genres/form.html", action="Update", genre=genre)

        try:
            db.execute("UPDATE genres SET name = ? WHERE id = ?", (name, genre_id))
            db.commit()
            flash(f"Genre '{name}' updated.", "success")
            return redirect(url_for("genres.index"))
        except Exception as e:
            flash(f"Error: {e}", "danger")

    return render_template("genres/form.html", action="Update", genre=genre)


@genres_bp.route("/<int:genre_id>/delete", methods=["POST"])
@login_required
@superuser_required
def delete(genre_id):
    db    = current_app.get_db()
    genre = db.execute("SELECT name FROM genres WHERE id = ?", (genre_id,)).fetchone()

    if genre is None:
        flash("Genre not found.", "danger")
        return redirect(url_for("genres.index"))

    try:
        db.execute("DELETE FROM genres WHERE id = ?", (genre_id,))
        db.commit()
        flash(f"Genre '{genre['name']}' deleted.", "success")
    except Exception as e:
        flash(f"Cannot delete: {e}", "danger")

    return redirect(url_for("genres.index"))
