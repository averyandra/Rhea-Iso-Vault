# Rhea ISO Vault

A lightweight, decoupled web application designed for indexing and managing local `.iso` files on a homelab server. Built with FastAPI for the backend REST API and a static HTML/Vanilla JS frontend served via Apache2, featuring a custom Red Glassmorphism dark theme.

---

## Features

- **Decoupled Architecture:** Pure REST API backend (FastAPI) and static frontend.
- **Zero-Upload Management:** Reads files directly from the physical storage directory (`/srv/rhea-iso`).
- **Automated Scanning:** Built-in background scheduler (APScheduler) synchronizes physical files with the database hourly.
- **Manual Trigger:** On-demand directory scanning via the web interface.
- **Smart Database Initialization:** Automatically creates the database and tables on the first startup if they do not exist.

---

## Prerequisites

- **OS:** Linux (Debian / Ubuntu / Fedora)
- **Web Server:** Apache2 (for serving static frontend)
- **Database:** MariaDB
- **Runtime:** Python 3.9+

---

## Directory Structure

```text
/opt/rhea-iso/
├── api/
│   ├── .env
│   ├── .env.example
│   ├── main.py
│   ├── requirements.txt
│   └── schema.sql
└── web/
    └── index.html
```

---

## Installation & Setup

### 1. Prepare Directories

Create the project structure and the target ISO storage directory:

```bash
sudo mkdir -p /opt/rhea-iso
sudo mkdir -p /srv/rhea-iso
sudo chown -R $USER:$USER /srv/rhea-iso
```

### 2. API Backend Setup

Navigate to the API directory, set up a virtual environment, and install dependencies:

```bash
cd /opt/rhea-iso/api
python3 -m venv rhea-env
source rhea-env/bin/activate
pip install -r requirements.txt
```

Configure the environment variables:

```bash
cp .env.example .env
nano .env
```

*(Update `DB_USER`, `DB_PASSWORD`, and ensure `ISO_DIRECTORY` points to `/srv/rhea-iso`).*

### 3. Frontend Setup (Apache2)

Symlink the web directory to your Apache web root:

```bash
sudo ln -s /opt/rhea-iso/web /var/www/rhea-iso
```

Ensure your Apache virtual host is configured to serve `/var/www/rhea-iso`. You may need to update the `API_BASE_URL` in `web/index.html` if you plan to expose the API under a specific domain or port.

---

## Running the Application

To start the API server manually:

```bash
cd /opt/rhea-iso/api
source rhea-env/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000
```

> **Note:** On the first startup, the API will read `schema.sql` and automatically initialize the `rhea` MariaDB database.

---

## Usage

1. Copy your `.iso` files into `/srv/rhea-iso`.
2. Access the web interface via your configured Apache local domain (e.g., `http://rhea.iso.local`).
3. Click **"Scan Directory"** to synchronize the database manually, or wait for the automatic hourly cron job.