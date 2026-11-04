# Server Monitor

Local demo for reading Linux server stats. Product requirements: [docs/requirements.md](docs/requirements.md).

The detail view reads CPU, memory, disk, network, and listening ports on this machine. It cannot change the machine. A saved server is a name and host in `data/servers.json`. Opening any saved server shows this machine's stats.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/flask --app app run --host 127.0.0.1 --port 5000
```

Open http://127.0.0.1:5000.

## Sign in

Generate a hash and put it in `.env`. `.env` stays untracked.

```bash
.venv/bin/python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('admin123'))"
```

```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<paste hash>
FLASK_SECRET_KEY=<any long random string>
```

Sign in as `admin` / `admin123`. `.env.example` shows the variable names.

## Servers

On the list page, add a display name and a hostname or IPv4 address. Remove opens a confirm step before the server is deleted.

## Live view

Each detail page refreshes about every 5 seconds and keeps about 5 minutes of samples in memory. A restart clears the charts and keeps the server list.

## Tests

GitHub Actions runs `pytest` on push and pull request. Locally:

```bash
.venv/bin/pip install pytest
.venv/bin/pytest
```
