# System Documentation — Music Database Manager

**Version:** 1.0  
**Framework:** Flask 3.x (Python)  
**Database:** SQLite 3  
**Author:** Manus AI

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Back-End: Flask Application](#3-back-end-flask-application)
   - 3.1 [Application Factory (`app.py`)](#31-application-factory-apppy)
   - 3.2 [Database Layer](#32-database-layer)
   - 3.3 [Blueprint System](#33-blueprint-system)
   - 3.4 [Routing and Request Lifecycle](#34-routing-and-request-lifecycle)
   - 3.5 [The Superuser Guard](#35-the-superuser-guard)
4. [User Management and Authentication](#4-user-management-and-authentication)
   - 4.1 [User Model](#41-user-model)
   - 4.2 [Login Flow](#42-login-flow)
   - 4.3 [Session Management](#43-session-management)
   - 4.4 [Logout Flow](#44-logout-flow)
   - 4.5 [Access Control Matrix](#45-access-control-matrix)
5. [Database Design](#5-database-design)
   - 5.1 [Entity-Relationship Model](#51-entity-relationship-model)
   - 5.2 [Table Definitions](#52-table-definitions)
   - 5.3 [Foreign Key Enforcement](#53-foreign-key-enforcement)
   - 5.4 [Seed Data](#54-seed-data)
   - 5.5 [Database Initialisation](#55-database-initialisation)
6. [Front-End: Templates and Styling](#6-front-end-templates-and-styling)
   - 6.1 [Template Inheritance](#61-template-inheritance)
   - 6.2 [The Base Layout (`base.html`)](#62-the-base-layout-basehtml)
   - 6.3 [Page Templates](#63-page-templates)
   - 6.4 [Sass Stylesheet Architecture](#64-sass-stylesheet-architecture)
   - 6.5 [Colour Palette and Design Tokens](#65-colour-palette-and-design-tokens)
7. [CRUD Operations in Detail](#7-crud-operations-in-detail)
   - 7.1 [Core Entities (Artists, Albums, Songs, Genres)](#71-core-entities-artists-albums-songs-genres)
   - 7.2 [Junction Tables (Associations)](#72-junction-tables-associations)
8. [Routing Reference](#8-routing-reference)
9. [Error Handling and Flash Messages](#9-error-handling-and-flash-messages)
10. [Security Considerations](#10-security-considerations)
11. [Performance Characteristics](#11-performance-characteristics)
12. [Extension Points](#12-extension-points)

---

## 1. System Overview

The Music Database Manager is a web application that provides a browser-based interface for performing Create, Read, Update, and Delete (CRUD) operations on a relational music catalogue. The catalogue models four core entities — **Artists**, **Albums**, **Songs**, and **Genres** — and three many-to-many relationships between them.

The application is built entirely on the Python ecosystem. Flask serves as the HTTP framework, SQLite as the embedded relational database engine, Jinja2 as the HTML templating engine, and Sass (compiled via libsass) as the stylesheet language. There is no JavaScript or TypeScript on the server side; all business logic runs in Python. The browser receives only HTML, CSS, and a minimal amount of inline JavaScript used exclusively for delete-confirmation dialogs.

The system enforces a two-tier access model: all authenticated users may browse, create, and edit records, but only the designated superuser (`sandro63`) may delete them. This constraint is applied at both the server level (via a Python decorator) and the presentation level (via conditional template rendering).

---

## 2. Architecture

The application follows a classic **server-side rendered (SSR)** architecture. Every page is a full HTML document generated on the server and sent to the browser in response to an HTTP request. There is no single-page application (SPA) layer, no REST API, and no client-side data fetching.

```
Browser
  │
  │  HTTP Request (GET / POST)
  ▼
Gunicorn (WSGI server)
  │
  ▼
Flask Application (app.py → create_app())
  │
  ├── Flask-Login middleware (session validation)
  │
  ├── Blueprint Router
  │     ├── auth.py
  │     ├── routes/home.py
  │     ├── routes/artists.py
  │     ├── routes/albums.py
  │     ├── routes/songs.py
  │     ├── routes/genres.py
  │     ├── routes/album_songs.py
  │     ├── routes/song_genres.py
  │     └── routes/album_genres.py
  │
  ├── SQLite (instance/music.db)
  │     └── Accessed via Python sqlite3 standard library
  │
  └── Jinja2 Template Engine
        └── templates/ → rendered HTML → HTTP Response → Browser
```

The request lifecycle is entirely synchronous. Flask handles one request at a time per worker process; Gunicorn spawns multiple worker processes to achieve concurrency.

---

## 3. Back-End: Flask Application

### 3.1 Application Factory (`app.py`)

The application is created using the **application factory pattern**, which is the recommended approach for Flask applications of any non-trivial size. Rather than creating the Flask instance at module level, a `create_app()` function is defined that instantiates and configures the application, then returns it. This pattern has two key advantages: it makes the application testable (each test can call `create_app()` with a different configuration), and it avoids circular import problems that arise when blueprints need to import from the application object.

```python
def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    # ... configuration, blueprint registration, etc.
    return app
```

The `instance_relative_config=True` argument tells Flask to look for the `instance/` folder (which holds the SQLite database file) relative to the application root, not the Python package root. This folder is excluded from version control via `.gitignore`.

### 3.2 Database Layer

The application uses Python's built-in `sqlite3` module directly, without an ORM. This is a deliberate design choice that keeps the dependency footprint minimal and makes the SQL queries fully transparent and auditable.

A helper function `get_db()` is attached to the Flask application object and retrieves a per-request database connection. SQLite connections are not thread-safe by default; Flask's application context (`g`) is used to store the connection so that it is created once per request and closed automatically when the request ends.

```python
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row   # rows behave like dicts
        g.db.execute('PRAGMA foreign_keys = ON')  # enforce FK constraints
    return g.db
```

Setting `row_factory = sqlite3.Row` is important: it means that query results can be accessed by column name (e.g., `row['title']`) rather than only by positional index, which makes template code far more readable.

The database is initialised on first run by `init_db()`, which reads and executes `music_database.sql`. This file contains both the DDL (table creation) and the DML (seed data insertion) using `INSERT OR IGNORE` to prevent duplicate seeding on subsequent startups.

### 3.3 Blueprint System

Flask **Blueprints** are used to organise the application into logical modules. Each entity has its own blueprint module in the `routes/` package. A blueprint is a collection of routes, error handlers, and template filters that can be registered on the application with a URL prefix.

| Blueprint | Module | URL Prefix | Responsibility |
|---|---|---|---|
| `auth` | `auth.py` | `/auth` | Login, logout |
| `home` | `routes/home.py` | `/` | Dashboard |
| `artists` | `routes/artists.py` | `/artists` | Artists CRUD |
| `albums` | `routes/albums.py` | `/albums` | Albums CRUD |
| `songs` | `routes/songs.py` | `/songs` | Songs CRUD |
| `genres` | `routes/genres.py` | `/genres` | Genres CRUD |
| `album_songs` | `routes/album_songs.py` | `/album-songs` | Album ↔ Songs |
| `song_genres` | `routes/song_genres.py` | `/song-genres` | Song ↔ Genres |
| `album_genres` | `routes/album_genres.py` | `/album-genres` | Album ↔ Genres |

All blueprints are registered in `create_app()` after the application object is configured. This means that blueprint code can safely import from `flask` (e.g., `current_app`, `g`, `request`) without triggering circular imports.

### 3.4 Routing and Request Lifecycle

Flask routes are defined using the `@blueprint.route()` decorator. Each route specifies one or more HTTP methods. The convention used throughout this application is:

- `GET` requests render a template and return HTML.
- `POST` requests process form data, perform a database operation, and redirect (following the **Post/Redirect/Get** pattern to prevent duplicate form submissions on browser refresh).

A typical CRUD route pair looks like this:

```python
@artists_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        db = current_app.get_db()
        db.execute('INSERT INTO artists (name, bio) VALUES (?, ?)', (name, bio))
        db.commit()
        flash('Artist created.', 'success')
        return redirect(url_for('artists.index'))   # PRG redirect
    return render_template('artists/form.html', action='Create', artist=None)
```

The `url_for()` function generates URLs from endpoint names (blueprint name + function name), which means URLs are never hard-coded in the application logic. If a URL prefix changes, only the blueprint registration needs to be updated.

### 3.5 The Superuser Guard

Delete operations are protected by a custom decorator, `@superuser_required`, defined in `auth.py`. The decorator checks whether the currently logged-in user has the `is_superuser` attribute set to `True`. If not, it aborts the request with HTTP 403 Forbidden.

```python
def superuser_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_superuser:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
```

This decorator is applied to every delete route in addition to `@login_required`. The order of decorators matters: `@login_required` is applied first (outermost), so unauthenticated users receive a redirect to the login page rather than a 403 error.

```python
@artists_bp.route('/<int:artist_id>/delete', methods=['POST'])
@login_required
@superuser_required
def delete(artist_id):
    ...
```

---

## 4. User Management and Authentication

### 4.1 User Model

Flask-Login requires a user object that implements four properties: `is_authenticated`, `is_active`, `is_anonymous`, and `get_id()`. The application defines a lightweight `User` class in `auth.py` that satisfies this interface. The class also carries a custom `is_superuser` boolean attribute that drives the access control logic.

```python
class User(UserMixin):
    def __init__(self, user_id, is_superuser=False):
        self.id = user_id
        self.is_superuser = is_superuser
```

`UserMixin` (from Flask-Login) provides default implementations of the four required properties, so the `User` class only needs to define `id` and any custom attributes.

User credentials are currently stored as a hard-coded dictionary in `auth.py`:

```python
USERS = {
    'sandro63': {'password': 'sandro63', 'is_superuser': True},
    'guest':    {'password': 'guest',    'is_superuser': False},
}
```

This is appropriate for a private tool or demonstration but should be replaced with a database-backed store and hashed passwords for any public-facing deployment. See the [Upgrading the User Store for Production](#upgrading-the-user-store-for-production) section of `implement.md`.

### 4.2 Login Flow

The login process follows these steps:

1. The browser sends a `GET /auth/login` request. Flask renders `templates/auth/login.html` and returns it.
2. The user fills in the username and password fields and submits the form.
3. The browser sends a `POST /auth/login` request with the form data in the request body.
4. Flask reads `request.form['username']` and `request.form['password']`.
5. The username is looked up in the `USERS` dictionary. If not found, or if the password does not match, a flash message is set and the login page is re-rendered.
6. If credentials are valid, a `User` object is constructed and passed to `login_user()` (Flask-Login). Flask-Login signs the user's ID into a session cookie and sends it to the browser.
7. Flask redirects the browser to the dashboard (`/`).

### 4.3 Session Management

Flask uses a **signed cookie** for session management. The session data (which includes the logged-in user's ID) is serialised, signed with the application's `SECRET_KEY` using HMAC-SHA1, and stored in a cookie named `session` on the client. The signature prevents tampering: if a user modifies the cookie value, the signature will no longer match and Flask will reject the session.

Flask-Login builds on top of Flask's session by storing the user ID in `session['_user_id']` and providing the `current_user` proxy object, which is available in all route functions and Jinja2 templates without any explicit import.

The `@login_required` decorator (from Flask-Login) checks whether `current_user.is_authenticated` is `True`. If not, it redirects the browser to the login URL (configured as `login_manager.login_view = 'auth.login'`).

### 4.4 Logout Flow

Logging out calls `logout_user()` (Flask-Login), which removes the user ID from the session. Flask then sends a `Set-Cookie` header that clears the session cookie on the browser. The user is redirected to the login page.

### 4.5 Access Control Matrix

The table below summarises which operations are available to each user type on each entity type.

| Operation | Unauthenticated | Authenticated User | Superuser (sandro63) |
|---|---|---|---|
| View list | Redirect to login | ✓ | ✓ |
| View create form | Redirect to login | ✓ | ✓ |
| Submit create form | Redirect to login | ✓ | ✓ |
| View edit form | Redirect to login | ✓ | ✓ |
| Submit edit form | Redirect to login | ✓ | ✓ |
| Submit delete form | Redirect to login | 403 Forbidden | ✓ |
| Delete button visible in UI | — | Hidden | Visible |

---

## 5. Database Design

### 5.1 Entity-Relationship Model

The database models four entities and three many-to-many relationships. The cardinalities are:

- An **Artist** has one or more **Albums** (one-to-many).
- An **Album** contains one or more **Songs**, and a **Song** can appear on one or more **Albums** (many-to-many via `album_songs`).
- A **Song** belongs to one or more **Genres** (many-to-many via `song_genres`).
- An **Album** belongs to zero or more **Genres** (many-to-many via `album_genres`).

```
artists (1) ──────< (N) albums
                         │
                         │ (N)
                         ▼
                    album_songs (junction)
                         │
                         │ (N)
                         ▼
songs (1) ──────────────< (N) album_songs
  │
  │ (N)
  ▼
song_genres (junction)
  │
  │ (N)
  ▼
genres (1) ──────────────< (N) song_genres
  │
  │ (N)
  ▼
album_genres (junction)
  │
  │ (N)
  ▼
albums (1) ──────────────< (N) album_genres
```

### 5.2 Table Definitions

**`artists`** — Core entity for recording artists or bands.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Surrogate key |
| `name` | TEXT | NOT NULL, UNIQUE | Artist or band name |
| `bio` | TEXT | | Optional biography |

**`albums`** — A collection of songs released together.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Surrogate key |
| `title` | TEXT | NOT NULL | Album title |
| `artist_id` | INTEGER | NOT NULL, FK → artists(id) | Owning artist |
| `release_year` | INTEGER | | Four-digit year |

**`songs`** — Individual musical tracks.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Surrogate key |
| `title` | TEXT | NOT NULL | Song title |
| `duration` | INTEGER | | Duration in seconds |

**`genres`** — A controlled vocabulary of musical genres.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Surrogate key |
| `name` | TEXT | NOT NULL, UNIQUE | Genre name |

**`album_songs`** — Junction table linking albums to songs (many-to-many).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `album_id` | INTEGER | NOT NULL, FK → albums(id) | Album reference |
| `song_id` | INTEGER | NOT NULL, FK → songs(id) | Song reference |
| — | — | PRIMARY KEY (album_id, song_id) | Prevents duplicates |

**`song_genres`** — Junction table linking songs to genres (many-to-many).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `song_id` | INTEGER | NOT NULL, FK → songs(id) | Song reference |
| `genre_id` | INTEGER | NOT NULL, FK → genres(id) | Genre reference |
| — | — | PRIMARY KEY (song_id, genre_id) | Prevents duplicates |

**`album_genres`** — Junction table linking albums to genres (many-to-many).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `album_id` | INTEGER | NOT NULL, FK → albums(id) | Album reference |
| `genre_id` | INTEGER | NOT NULL, FK → genres(id) | Genre reference |
| — | — | PRIMARY KEY (album_id, genre_id) | Prevents duplicates |

### 5.3 Foreign Key Enforcement

SQLite does not enforce foreign key constraints by default; they must be explicitly enabled per connection with `PRAGMA foreign_keys = ON`. The application executes this pragma immediately after opening every database connection in `get_db()`. This ensures that:

- An album cannot be created with an `artist_id` that does not exist in `artists`.
- An `album_songs` row cannot reference a non-existent album or song.
- Deleting an artist that still has albums will raise an `IntegrityError` (caught by the route and reported as a flash message).

### 5.4 Seed Data

The `music_database.sql` file populates the database with a representative initial dataset:

| Entity | Count | Examples |
|---|---|---|
| Artists | 3 | The Beatles, Led Zeppelin, Pink Floyd |
| Albums | 4 | *Abbey Road*, *Sgt. Pepper's*, *Led Zeppelin IV*, *The Dark Side of the Moon* |
| Songs | 48 | All tracks from the four albums above |
| Genres | 4 | Rock, Psychedelic Rock, Hard Rock, Folk Rock |
| Album ↔ Song links | 48 | Each song linked to its album |
| Song ↔ Genre links | 52 | Songs tagged with one or more genres |
| Album ↔ Genre links | 7 | Albums tagged with one or more genres |

All seed insertions use `INSERT OR IGNORE` so that running the initialisation script a second time (e.g., after a server restart) does not produce duplicate rows or errors.

### 5.5 Database Initialisation

The database is initialised automatically on first run by the `init_db()` function, which is called from `create_app()` via Flask's `with app.app_context()` block. The function:

1. Creates the `instance/` directory if it does not exist.
2. Opens a connection to `instance/music.db`.
3. Reads `music_database.sql` from the project root.
4. Executes the entire script using `executescript()`.
5. Commits and closes the connection.

Because `executescript()` executes multiple SQL statements in a single call, the `PRAGMA foreign_keys = ON` statement at the top of the SQL file is also executed during initialisation, ensuring that the seed data itself respects referential integrity.

---

## 6. Front-End: Templates and Styling

### 6.1 Template Inheritance

Jinja2's template inheritance system is used to avoid repeating the HTML boilerplate (DOCTYPE, `<head>`, sidebar, topbar, flash message rendering) on every page. The inheritance hierarchy is flat: all page templates extend `base.html` directly.

```
base.html
  ├── home.html
  ├── auth/login.html   (standalone — does not extend base.html)
  ├── artists/index.html
  ├── artists/form.html
  ├── albums/index.html
  ├── albums/form.html
  ├── songs/index.html
  ├── songs/form.html
  ├── genres/index.html
  ├── genres/form.html
  ├── album_songs/index.html
  ├── song_genres/index.html
  └── album_genres/index.html
```

The login page (`auth/login.html`) is the only template that does not extend `base.html`, because it has its own full-page centred layout that does not include the sidebar or topbar.

### 6.2 The Base Layout (`base.html`)

`base.html` defines the overall page structure and exposes four blocks for child templates to override:

| Block | Purpose | Default content |
|---|---|---|
| `title` | The `<title>` tag prefix | `"Music DB"` |
| `topbar_title` | The heading in the top bar | *(empty)* |
| `topbar_actions` | Buttons on the right of the top bar | *(empty)* |
| `content` | The main page body | *(empty)* |

The sidebar is rendered unconditionally in `base.html` and uses `request.blueprint` and `request.endpoint` to apply the `sidebar__link--active` CSS class to the currently active navigation item. The `current_user` proxy (injected by Flask-Login) is used to display the username, the superuser/user badge, and to conditionally show the sign-out link.

### 6.3 Page Templates

Each entity has two templates: an `index.html` (list view) and a `form.html` (create/edit form). The form template is shared between the create and edit operations; the `action` variable (passed from the route function as `"Create"` or `"Update"`) controls the form title and submit button label, and the `artist` / `album` / `song` / `genre` variable (passed as `None` for create, or a database row for edit) pre-populates the form fields.

Junction table pages (`album_songs`, `song_genres`, `album_genres`) have a single `index.html` template that combines the association list table with an inline add-association form at the top of the page.

### 6.4 Sass Stylesheet Architecture

All styles are authored in a single file, `static/scss/main.scss`, using Sass (SCSS syntax). The file is compiled to `static/css/main.css` by the `build_css.py` script, which uses the `libsass` Python binding to the LibSass C library. The compiled CSS is committed to the repository so that the application can be run without a Sass compilation step.

The SCSS file is organised into clearly labelled sections:

| Section | Contents |
|---|---|
| Colour palette | Sass variables for all colours (`$green-dark`, `$orange-mid`, etc.) |
| Typography | Font stack and base sizes |
| Spacing | Sidebar width, header height, border radius, gap |
| Reset & base | Box-sizing reset, `html`/`body` defaults, link styles |
| Layout shell | `.layout` flex container |
| Sidebar | `.sidebar` and all child elements |
| Main content area | `.main`, `.topbar`, `.content` |
| Flash messages | `.flash-list`, `.flash--success`, `.flash--danger`, etc. |
| Dashboard cards | `.dashboard-grid`, `.stat-card` |
| Data table | `table`, `th`, `td`, `.table-wrap` |
| Buttons | `.btn`, `.btn--primary`, `.btn--danger`, `.btn--sm` |
| Forms | `.form-card`, `.form-group`, `.form-actions` |
| Login page | `.login-page`, `.login-card` |
| Badge | `.badge--superuser`, `.badge--user` |
| Junction add-form row | `.add-row` |

Sass's **BEM-inspired naming** (e.g., `.sidebar__link`, `.sidebar__link--active`, `.stat-card__count`) is used throughout to keep selector specificity low and make the relationship between elements explicit.

### 6.5 Colour Palette and Design Tokens

All colours are defined as Sass variables at the top of `main.scss`. This means that changing the colour scheme requires editing only the variable declarations; all derived rules update automatically on the next compilation.

| Variable | Hex value | Usage |
|---|---|---|
| `$green-dark` | `#1b5e20` | Sidebar background, table headers |
| `$green-mid` | `#2e7d32` | Primary buttons, active links |
| `$green-light` | `#e8f5e9` | Page background, table row hover |
| `$green-border` | `#a5d6a7` | Card and table borders |
| `$orange-dark` | `#e65100` | Delete buttons |
| `$orange-mid` | `#f57c00` | Active nav item, superuser badge, avatar |
| `$orange-light` | `#fff3e0` | Warning flash message background |

---

## 7. CRUD Operations in Detail

### 7.1 Core Entities (Artists, Albums, Songs, Genres)

All four core entities follow the same CRUD pattern. The following description uses Artists as the canonical example; Albums, Songs, and Genres are identical in structure.

**List (Read).** The `index()` route executes a `SELECT` query (with a `JOIN` for Albums, to include the artist name) and passes the result set to the index template. The template iterates over the rows with a Jinja2 `{% for %}` loop and renders one table row per record.

**Create.** The `create()` route handles both `GET` (render the empty form) and `POST` (process the submission). On `POST`, the route reads `request.form`, validates that required fields are non-empty, executes an `INSERT` statement, commits the transaction, sets a success flash message, and redirects to the list page.

**Update.** The `edit()` route also handles both `GET` and `POST`. On `GET`, it fetches the existing record by primary key and passes it to the form template, which pre-populates the input fields. On `POST`, it executes an `UPDATE` statement and redirects.

**Delete.** The `delete()` route accepts only `POST` requests (delete forms in the templates use `method="POST"`). It executes a `DELETE` statement and redirects. The route is protected by both `@login_required` and `@superuser_required`.

All database write operations are wrapped in a `try/except` block that catches `sqlite3.IntegrityError` (raised when a foreign key constraint is violated, e.g., attempting to delete an artist that still has albums) and reports the error as a flash message rather than crashing.

### 7.2 Junction Tables (Associations)

The three junction table pages (`album_songs`, `song_genres`, `album_genres`) combine the list and add-form on a single page. This design avoids the need for a separate create form page for what is essentially a two-field record.

**List.** A `SELECT` with two `JOIN` clauses retrieves the human-readable names for both sides of the association (e.g., album title and song title rather than raw integer IDs).

**Add.** The add form presents two `<select>` dropdowns populated from the corresponding entity tables. On submission, an `INSERT` statement is executed. The composite primary key on the junction table prevents duplicate associations; a duplicate insertion raises an `IntegrityError`, which is caught and reported as a flash message.

**Remove.** The remove operation is a `DELETE` statement keyed on both foreign key columns. It is protected by `@superuser_required`. Each row in the junction table list includes a small Remove form (visible only to the superuser) with hidden inputs carrying the two foreign key values.

---

## 8. Routing Reference

The complete URL routing table for the application is as follows. All routes except `/auth/login` require authentication.

| Method | URL | Endpoint | Access | Description |
|---|---|---|---|---|
| GET | `/auth/login` | `auth.login` | Public | Render login form |
| POST | `/auth/login` | `auth.login` | Public | Process login |
| GET | `/auth/logout` | `auth.logout` | Authenticated | Log out and redirect |
| GET | `/` | `home.index` | Authenticated | Dashboard |
| GET | `/artists/` | `artists.index` | Authenticated | List artists |
| GET | `/artists/new` | `artists.create` | Authenticated | New artist form |
| POST | `/artists/new` | `artists.create` | Authenticated | Create artist |
| GET | `/artists/<id>/edit` | `artists.edit` | Authenticated | Edit artist form |
| POST | `/artists/<id>/edit` | `artists.edit` | Authenticated | Update artist |
| POST | `/artists/<id>/delete` | `artists.delete` | **Superuser** | Delete artist |
| GET | `/albums/` | `albums.index` | Authenticated | List albums |
| GET | `/albums/new` | `albums.create` | Authenticated | New album form |
| POST | `/albums/new` | `albums.create` | Authenticated | Create album |
| GET | `/albums/<id>/edit` | `albums.edit` | Authenticated | Edit album form |
| POST | `/albums/<id>/edit` | `albums.edit` | Authenticated | Update album |
| POST | `/albums/<id>/delete` | `albums.delete` | **Superuser** | Delete album |
| GET | `/songs/` | `songs.index` | Authenticated | List songs |
| GET | `/songs/new` | `songs.create` | Authenticated | New song form |
| POST | `/songs/new` | `songs.create` | Authenticated | Create song |
| GET | `/songs/<id>/edit` | `songs.edit` | Authenticated | Edit song form |
| POST | `/songs/<id>/edit` | `songs.edit` | Authenticated | Update song |
| POST | `/songs/<id>/delete` | `songs.delete` | **Superuser** | Delete song |
| GET | `/genres/` | `genres.index` | Authenticated | List genres |
| GET | `/genres/new` | `genres.create` | Authenticated | New genre form |
| POST | `/genres/new` | `genres.create` | Authenticated | Create genre |
| GET | `/genres/<id>/edit` | `genres.edit` | Authenticated | Edit genre form |
| POST | `/genres/<id>/edit` | `genres.edit` | Authenticated | Update genre |
| POST | `/genres/<id>/delete` | `genres.delete` | **Superuser** | Delete genre |
| GET | `/album-songs/` | `album_songs.index` | Authenticated | List + add form |
| POST | `/album-songs/add` | `album_songs.add` | Authenticated | Add association |
| POST | `/album-songs/remove` | `album_songs.remove` | **Superuser** | Remove association |
| GET | `/song-genres/` | `song_genres.index` | Authenticated | List + add form |
| POST | `/song-genres/add` | `song_genres.add` | Authenticated | Add association |
| POST | `/song-genres/remove` | `song_genres.remove` | **Superuser** | Remove association |
| GET | `/album-genres/` | `album_genres.index` | Authenticated | List + add form |
| POST | `/album-genres/add` | `album_genres.add` | Authenticated | Add association |
| POST | `/album-genres/remove` | `album_genres.remove` | **Superuser** | Remove association |

---

## 9. Error Handling and Flash Messages

Flask's `flash()` function is used to communicate the outcome of every write operation to the user. Flash messages are stored in the session and consumed (and cleared) on the next request. The `base.html` template renders all pending flash messages at the top of the content area on every page load.

Four message categories are used, each with a distinct visual style:

| Category | CSS class | Colour | Used for |
|---|---|---|---|
| `success` | `.flash--success` | Green | Successful create, update, or delete |
| `danger` | `.flash--danger` | Red | Validation errors, integrity violations |
| `warning` | `.flash--warning` | Orange | Non-critical warnings |
| `info` | `.flash--info` | Blue | Informational notices |

Database `IntegrityError` exceptions (e.g., duplicate unique values, foreign key violations) are caught in every write route and converted to `danger` flash messages, so the user receives a meaningful explanation rather than a 500 Internal Server Error page.

---

## 10. Security Considerations

**Session signing.** Flask signs the session cookie with `SECRET_KEY`. In production, this key must be a long, randomly generated string stored as an environment variable, never committed to version control.

**SQL injection prevention.** All database queries use parameterised statements (the `?` placeholder syntax of the `sqlite3` module). User-supplied input is never interpolated directly into SQL strings.

**CSRF protection.** The application does not currently implement Cross-Site Request Forgery (CSRF) tokens. For a private tool on a trusted network this is acceptable, but a public-facing deployment should add Flask-WTF or a manual CSRF token to all POST forms.

**Password storage.** Passwords are currently stored in plain text in the `USERS` dictionary. A production deployment must use `werkzeug.security.generate_password_hash` and `check_password_hash` (or an equivalent) to store only salted hashes.

**Delete confirmation.** All delete forms include a JavaScript `confirm()` dialog (`onsubmit="return confirm(...)"`) as a client-side safeguard against accidental deletion. This is a UX measure only; the server-side `@superuser_required` decorator is the authoritative access control mechanism.

**Foreign key cascades.** The schema does not use `ON DELETE CASCADE`. Attempting to delete a parent record (e.g., an artist with albums) will raise an `IntegrityError`, which is caught and reported as a flash message. This is a conservative choice that prevents accidental data loss.

---

## 11. Performance Characteristics

The application is designed for a small to medium catalogue (thousands of records) on a single-server deployment. The following characteristics are relevant:

**No pagination.** All list views return every row in the table in a single query. For catalogues with tens of thousands of songs, server-side pagination (using `LIMIT` and `OFFSET`) should be added.

**No caching.** Every page load executes fresh database queries. For read-heavy workloads, Flask-Caching with a simple in-memory backend could be added with minimal code changes.

**SQLite concurrency.** SQLite uses file-level locking. Write operations (INSERT, UPDATE, DELETE) acquire an exclusive lock on the database file, which means concurrent writes from multiple Gunicorn workers will serialise. For a music catalogue management tool with a small number of concurrent users, this is not a practical limitation. For high-concurrency workloads, migrating to PostgreSQL (with SQLAlchemy as the ORM layer) is the recommended path.

**Static file serving.** In development, Flask serves static files directly. In production (Nginx + Gunicorn), Nginx serves the `static/` directory directly, bypassing the Python application entirely, which is significantly faster.

---

## 12. Extension Points

The application is designed to be extended incrementally. The following enhancements are the most natural next steps:

**Database-backed user management.** Add a `users` table to `music_database.sql`, replace the `USERS` dictionary in `auth.py` with database queries, and add a registration or CLI-based user creation flow.

**Server-side search and pagination.** Add a `?q=` query parameter to list routes and use `WHERE title LIKE ?` in the SQL queries. Add `LIMIT` and `OFFSET` for pagination.

**Song duration formatting.** The `songs` table stores duration in seconds (an integer). A Jinja2 custom filter (registered in `create_app()`) could format this as `m:ss` for display without changing the stored value.

**REST API layer.** Flask Blueprints make it straightforward to add a `/api/v1/` blueprint that returns JSON responses for the same data, enabling integration with mobile apps or third-party tools.

**PostgreSQL migration.** Replacing SQLite with PostgreSQL requires changing the `sqlite3` calls to `psycopg2` (or using SQLAlchemy as an abstraction layer), updating the placeholder syntax from `?` to `%s`, and adjusting the schema DDL for PostgreSQL syntax. The application's use of raw SQL (rather than an ORM) makes this migration explicit and auditable.

**Full-text search.** SQLite's built-in FTS5 extension can be used to add full-text search across song titles, artist names, and album titles with minimal changes to the schema and query layer.
