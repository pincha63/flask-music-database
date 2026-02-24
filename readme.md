# Music Database Manager

A full-stack web application for managing a music catalogue — artists, albums, songs, and genres — built with **Flask**, **SQLite**, **Jinja2**, and **Sass**. All server-side logic is written in Python; there is no JavaScript or TypeScript backend.

---

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [User Accounts](#user-accounts)
- [Database Schema](#database-schema)
- [Routing Overview](#routing-overview)
- [Styling](#styling)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Full CRUD** on all seven database entities: Artists, Albums, Songs, Genres, Album ↔ Songs, Song ↔ Genres, and Album ↔ Genres.
- **Role-based access control**: Create and Edit operations are available to all authenticated users; Delete operations are restricted to the superuser (`sandro63`).
- **Relational integrity**: SQLite foreign key constraints are enforced on every connection via `PRAGMA foreign_keys = ON`.
- **No front-end framework**: all styles are hand-written Sass (SCSS), compiled to a single CSS file by `libsass`.
- **Session-based authentication** via Flask-Login with a secure, signed cookie.
- **Commented source code** throughout — every module, route, and template block is annotated.
- **Pre-seeded database** with three artists (The Beatles, Led Zeppelin, Pink Floyd), four albums, 48 songs, and four genres.

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Web framework | [Flask](https://flask.palletsprojects.com/) | ≥ 3.0 |
| Database engine | [SQLite](https://www.sqlite.org/) | (bundled with Python) |
| Database access | Python `sqlite3` standard library | — |
| Authentication | [Flask-Login](https://flask-login.readthedocs.io/) | ≥ 0.6 |
| Templating | Jinja2 (bundled with Flask) | — |
| Stylesheet language | [Sass (SCSS)](https://sass-lang.com/) via [libsass](https://github.com/sass/libsass-python) | ≥ 0.23 |
| Production server | [Gunicorn](https://gunicorn.org/) | ≥ 21.0 |
| Python | CPython | ≥ 3.10 |

---

## Project Structure

```
flask-music-app/
│
├── app.py                  # Application factory, DB helpers, blueprint registration
├── auth.py                 # User model, login/logout routes, @superuser_required
├── build_css.py            # Compiles static/scss/main.scss → static/css/main.css
├── music_database.sql      # SQLite schema (DDL) + seed data (DML)
├── requirements.txt        # Python dependencies
├── .gitignore
│
├── routes/                 # One Blueprint module per entity
│   ├── __init__.py
│   ├── home.py             # Dashboard (record counts)
│   ├── artists.py          # Artists CRUD
│   ├── albums.py           # Albums CRUD
│   ├── songs.py            # Songs CRUD
│   ├── genres.py           # Genres CRUD
│   ├── album_songs.py      # Album ↔ Songs junction
│   ├── song_genres.py      # Song ↔ Genres junction
│   └── album_genres.py     # Album ↔ Genres junction
│
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Master layout (sidebar, topbar, flash messages)
│   ├── home.html           # Dashboard page
│   ├── auth/
│   │   └── login.html
│   ├── artists/
│   │   ├── index.html
│   │   └── form.html
│   ├── albums/
│   │   ├── index.html
│   │   └── form.html
│   ├── songs/
│   │   ├── index.html
│   │   └── form.html
│   ├── genres/
│   │   ├── index.html
│   │   └── form.html
│   ├── album_songs/
│   │   └── index.html
│   ├── song_genres/
│   │   └── index.html
│   └── album_genres/
│       └── index.html
│
└── static/
    ├── scss/
    │   └── main.scss       # Sass source (green + orange palette)
    └── css/
        └── main.css        # Compiled CSS (committed for convenience)
```

---

## Quick Start

### Prerequisites

- Python 3.10 or later
- `pip`

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/flask-music-app.git
cd flask-music-app

# 2. Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Recompile the SCSS if you have edited it
python3 build_css.py

# 5. Run the development server
flask --app app run --debug
```

The application will be available at `http://127.0.0.1:5000`. On first run it will automatically create the SQLite database at `instance/music.db` and seed it with demo data.

---

## User Accounts

The application ships with two hard-coded demo accounts. In a production deployment these should be replaced with a proper user-management system backed by a database table.

| Username | Password | Role |
|---|---|---|
| `sandro63` | `sandro63` | **Superuser** — can Create, Read, Update, and Delete |
| `guest` | `guest` | **User** — can Create, Read, and Update only |

The superuser check is enforced at two levels: the `@superuser_required` decorator on every delete route (server side), and conditional rendering of the Delete button in every template (client side).

---

## Database Schema

The database contains seven tables. The four core tables hold entity data; the three junction tables model many-to-many relationships.

```
artists ──< albums ──< album_songs >── songs ──< song_genres >── genres
                  └──< album_genres >── genres
```

All foreign key constraints are declared with `ON DELETE CASCADE` where appropriate. `PRAGMA foreign_keys = ON` is executed on every new connection.

---

## Routing Overview

| Method | URL | Blueprint | Description |
|---|---|---|---|
| GET / POST | `/auth/login` | `auth` | Login form |
| GET | `/auth/logout` | `auth` | Logout and redirect |
| GET | `/` | `home` | Dashboard |
| GET | `/artists/` | `artists` | List artists |
| GET | `/artists/new` | `artists` | New artist form |
| POST | `/artists/new` | `artists` | Create artist |
| GET | `/artists/<id>/edit` | `artists` | Edit artist form |
| POST | `/artists/<id>/edit` | `artists` | Update artist |
| POST | `/artists/<id>/delete` | `artists` | Delete artist *(superuser only)* |
| … | *(same pattern for albums, songs, genres)* | | |
| GET | `/album-songs/` | `album_songs` | List + add form |
| POST | `/album-songs/add` | `album_songs` | Add association |
| POST | `/album-songs/remove` | `album_songs` | Remove association *(superuser only)* |
| … | *(same pattern for song-genres, album-genres)* | | |

---

## Styling

All styles are authored in `static/scss/main.scss` using Sass (SCSS syntax). The file is compiled to `static/css/main.css` by running:

```bash
python3 build_css.py
```

No CSS framework (Bootstrap, Tailwind, etc.) is used. The colour palette is built around **forest green** (`#2e7d32`) and **deep orange** (`#f57c00`), with semantic variables defined as Sass variables at the top of `main.scss`.

---

## Contributing

1. Fork the repository and create a feature branch.
2. Make your changes, ensuring all routes remain commented.
3. Run `python3 build_css.py` if you modified the SCSS.
4. Open a pull request with a clear description of the change.

---

## License

This project is released under the [MIT License](https://opensource.org/licenses/MIT).
