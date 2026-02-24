# Deployment Guide — Music Database Manager

This document provides step-by-step instructions for deploying the Music Database Manager on three popular hosting platforms that support Python/Flask applications: **Railway**, **Render**, and **PythonAnywhere**. A section on self-hosted VPS (Ubuntu + Nginx + Gunicorn) is also included for teams that prefer full infrastructure control.

---

## Table of Contents

- [Before You Begin](#before-you-begin)
- [Option A — Railway](#option-a--railway)
- [Option B — Render](#option-b--render)
- [Option C — PythonAnywhere](#option-c--pythonanywhere)
- [Option D — Self-Hosted VPS (Ubuntu + Nginx + Gunicorn)](#option-d--self-hosted-vps-ubuntu--nginx--gunicorn)
- [Environment Variables Reference](#environment-variables-reference)
- [Post-Deployment Checklist](#post-deployment-checklist)
- [Upgrading the User Store for Production](#upgrading-the-user-store-for-production)

---

## Before You Begin

Regardless of hosting platform, complete these steps first.

**1. Compile the CSS.** The compiled `static/css/main.css` is included in the repository, but if you have modified `static/scss/main.scss`, regenerate it before deploying:

```bash
python3 build_css.py
```

**2. Set a strong secret key.** The application reads `SECRET_KEY` from the environment. Never use the default development value in production. Generate a secure key with:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**3. Review the user store.** The current implementation uses two hard-coded accounts (`sandro63` and `guest`). For any public-facing deployment, replace this with a database-backed user table before going live. See [Upgrading the User Store for Production](#upgrading-the-user-store-for-production).

**4. Understand the database file.** The application uses SQLite and stores the database at `instance/music.db`. On platforms with an ephemeral filesystem (Railway, Render free tier), the database is reset on every deployment. For persistent data, mount a volume (Railway/Render) or switch to PostgreSQL.

---

## Option A — Railway

[Railway](https://railway.app) is a modern platform-as-a-service that supports Python natively and provides persistent volume mounts.

### Steps

**1. Push your code to GitHub.** Railway deploys directly from a Git repository.

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/flask-music-app.git
git push -u origin main
```

**2. Create a new Railway project.** Log in at [railway.app](https://railway.app), click **New Project → Deploy from GitHub repo**, and select your repository.

**3. Add a `Procfile`.** Railway uses this to determine the start command. Create the file at the project root:

```
web: gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2
```

**4. Set environment variables.** In the Railway dashboard, go to your service → **Variables** and add:

| Variable | Value |
|---|---|
| `SECRET_KEY` | *(your generated 64-char hex string)* |
| `FLASK_ENV` | `production` |

**5. Mount a persistent volume (optional but recommended).** In the Railway dashboard, go to **Volumes**, create a new volume, and mount it at `/app/instance`. This ensures the SQLite database survives redeployments.

**6. Deploy.** Railway will automatically build and deploy on every push to `main`. The public URL is shown in the dashboard under **Deployments**.

---

## Option B — Render

[Render](https://render.com) offers a free tier for web services and supports Python/Gunicorn out of the box.

### Steps

**1. Push your code to GitHub** (same as Railway step 1 above).

**2. Create a new Web Service.** In the Render dashboard, click **New → Web Service**, connect your GitHub account, and select the repository.

**3. Configure the service.**

| Setting | Value |
|---|---|
| Environment | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2` |
| Instance Type | Free (or Starter for persistent disk) |

**4. Add environment variables.** Under **Environment**, add `SECRET_KEY` and `FLASK_ENV=production`.

**5. Add a persistent disk (Render paid plans).** Under **Disks**, add a disk mounted at `/opt/render/project/src/instance` with at least 1 GB. This preserves `music.db` across deploys.

**6. Deploy.** Click **Create Web Service**. Render will install dependencies, start Gunicorn, and provide a public `*.onrender.com` URL.

> **Note on the free tier:** Render free-tier web services spin down after 15 minutes of inactivity and take ~30 seconds to wake up on the next request. The free tier also has an ephemeral filesystem, meaning the SQLite database is reset on each deploy.

---

## Option C — PythonAnywhere

[PythonAnywhere](https://www.pythonanywhere.com) is a browser-based Python hosting platform that is particularly well-suited to Flask applications and provides a persistent filesystem on all plans, including the free tier.

### Steps

**1. Create a PythonAnywhere account** at [pythonanywhere.com](https://www.pythonanywhere.com).

**2. Upload your project.** Open a **Bash console** from the dashboard and clone your repository:

```bash
git clone https://github.com/your-username/flask-music-app.git ~/flask-music-app
```

Alternatively, use the **Files** tab to upload a zip archive and unzip it:

```bash
unzip flask-music-app.zip
```

**3. Create a virtual environment.**

```bash
cd ~/flask-music-app
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**4. Configure a Web App.** Go to the **Web** tab → **Add a new web app** → **Manual configuration** → select **Python 3.11**.

**5. Set the WSGI file.** PythonAnywhere provides a WSGI configuration file at `/var/www/<username>_pythonanywhere_com_wsgi.py`. Replace its entire contents with:

```python
import sys
import os

# Add the project directory to the Python path
project_home = '/home/<your-username>/flask-music-app'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set the secret key via environment variable
os.environ['SECRET_KEY'] = 'your-secret-key-here'
os.environ['FLASK_ENV'] = 'production'

# Import the Flask application factory
from app import create_app
application = create_app()
```

Replace `<your-username>` and the secret key value accordingly.

**6. Set the virtual environment path.** In the Web tab, under **Virtualenv**, enter:

```
/home/<your-username>/flask-music-app/.venv
```

**7. Set static files mapping.** In the Web tab, under **Static files**, add:

| URL | Directory |
|---|---|
| `/static/` | `/home/<your-username>/flask-music-app/static` |

**8. Reload the web app.** Click the green **Reload** button in the Web tab. Your app will be live at `https://<your-username>.pythonanywhere.com`.

> **PythonAnywhere free tier note:** The free tier provides a persistent filesystem and a `*.pythonanywhere.com` subdomain. It does not allow outbound internet connections from the app itself (only whitelisted domains), but this application does not require any external network calls.

---

## Option D — Self-Hosted VPS (Ubuntu + Nginx + Gunicorn)

This option gives you full control and is suitable for production workloads. The instructions assume a fresh Ubuntu 22.04 server.

### 1. Provision the server

Create a VPS with at least 512 MB RAM at any provider (DigitalOcean, Linode, Hetzner, etc.). SSH in as root and create a non-root user:

```bash
adduser deploy
usermod -aG sudo deploy
su - deploy
```

### 2. Install system dependencies

```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip nginx git
```

### 3. Clone and set up the project

```bash
cd /var/www
sudo git clone https://github.com/your-username/flask-music-app.git
sudo chown -R deploy:deploy flask-music-app
cd flask-music-app
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Create a systemd service

Create `/etc/systemd/system/music-app.service`:

```ini
[Unit]
Description=Music Database Manager (Gunicorn)
After=network.target

[Service]
User=deploy
Group=www-data
WorkingDirectory=/var/www/flask-music-app
Environment="SECRET_KEY=your-secret-key-here"
Environment="FLASK_ENV=production"
ExecStart=/var/www/flask-music-app/.venv/bin/gunicorn \
    "app:create_app()" \
    --bind unix:/run/music-app.sock \
    --workers 3 \
    --timeout 60 \
    --access-logfile /var/log/music-app/access.log \
    --error-logfile /var/log/music-app/error.log
Restart=always

[Install]
WantedBy=multi-user.target
```

Create the log directory and enable the service:

```bash
sudo mkdir -p /var/log/music-app
sudo chown deploy:www-data /var/log/music-app
sudo systemctl daemon-reload
sudo systemctl enable music-app
sudo systemctl start music-app
```

### 5. Configure Nginx as a reverse proxy

Create `/etc/nginx/sites-available/music-app`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Serve static files directly from Nginx (faster than Flask)
    location /static/ {
        alias /var/www/flask-music-app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy all other requests to Gunicorn
    location / {
        proxy_pass http://unix:/run/music-app.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and reload Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/music-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Enable HTTPS with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Certbot will automatically modify the Nginx configuration and set up auto-renewal.

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | **Yes** | `dev-secret-key` (insecure) | Signs the session cookie. Must be a long random string in production. |
| `FLASK_ENV` | No | `development` | Set to `production` to disable the debugger and enable optimisations. |
| `DATABASE_PATH` | No | `instance/music.db` | Absolute or relative path to the SQLite database file. Override to use a mounted volume path. |

---

## Post-Deployment Checklist

After deploying, verify the following:

- [ ] The login page loads at `/auth/login`.
- [ ] Signing in as `sandro63` shows the orange **SUPERUSER** badge in the sidebar.
- [ ] Signing in as `guest` hides all Delete buttons.
- [ ] Creating a new artist, album, song, and genre works without errors.
- [ ] Editing an existing record saves correctly.
- [ ] Attempting to access a delete URL as `guest` returns a 403 response.
- [ ] The dashboard record counts match the expected seed data (3 artists, 4 albums, 48 songs, 4 genres).
- [ ] `SECRET_KEY` is set to a value that is not the default `dev-secret-key`.
- [ ] HTTPS is active and HTTP redirects to HTTPS (VPS option).

---

## Upgrading the User Store for Production

The current implementation stores user credentials as a hard-coded Python dictionary in `auth.py`. This is acceptable for a private tool but is not suitable for a public-facing application. To upgrade to a database-backed user store:

**1.** Add a `users` table to `music_database.sql`:

```sql
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE,
    password_hash TEXT  NOT NULL,
    is_superuser INTEGER NOT NULL DEFAULT 0
);
```

**2.** Install `werkzeug` (already a Flask dependency) and use `generate_password_hash` / `check_password_hash` for credential storage.

**3.** Replace the `USERS` dictionary in `auth.py` with database queries using `get_db()`.

**4.** Add a registration route (or a CLI command using `flask shell`) to create the initial superuser account.
