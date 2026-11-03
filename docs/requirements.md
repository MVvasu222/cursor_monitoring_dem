# Demo Server Monitoring — Requirements

Local demo for internal teams who today sign in to Linux servers to check CPU, memory, disk, network, and ports. The app runs on the Linux machine where Cursor is running. It is read-only toward that machine.

## Users

L1, L2, and L3 in infrastructure and application development. Everyone uses the same view. The demo has one account and no separate roles.

## What this demo does

- Sign in as `admin` with a hashed password.
- Add and remove Linux servers in the app (display name and hostname or IP).
- Show live CPU, memory, disk, network, and listening ports.
- Refresh about every 5 seconds and keep a short chart of the last 5 minutes.

The server list is saved on disk. Chart history stays in memory and starts over when the app restarts.

## Demo data rule

Metrics are read on the machine that runs the app. Saving a server stores its name and host and shows those labels in the UI. Opening any saved server shows this machine’s live stats. The demo does not open SSH or install an agent.

## Sign in

- Username is `admin`.
- The password is stored only as a hash in a local `.env` file. The app reads it at startup.
- Hash format is Werkzeug (`generate_password_hash` / `check_password_hash`).
- A signed-in session is required for every page except the sign-in page.
- A wrong password shows a short error and stays on the sign-in page.
- Sign out ends the session.

Demo password for local use: `admin123`. Only the hash goes in `.env`. `.env` stays off git. `.env.example` documents the variable names.

## Servers

An operator can:

- Add a server with a display name and a hostname or IPv4 address. Both fields are required.
- See the saved list (name and host).
- Remove a server after a confirm step. Removal deletes the saved record only.

Reject a duplicate hostname or IP. The list is stored in a local JSON file so it survives a restart.

## Monitoring view

Each server page shows the current sample and a line chart of about the last 5 minutes (one point per refresh).

| Area | Current values | Chart |
| --- | --- | --- |
| CPU | Overall percent; load average 1, 5, and 15 | CPU percent |
| Memory | Used, free, and percent | Memory percent |
| Disk | Used, free, and percent for each mounted filesystem | Root filesystem (`/`) percent |
| Network | Per interface: bytes in, bytes out, and rate since the previous sample | Total send and receive rate |
| Ports | Listening ports: port, protocol, address, process name | None |

The page updates in place about every 5 seconds. A failed sample shows a short error and keeps the last good sample on screen.

## Read-only

The UI is for viewing. It has no controls to change the host: no process kill, service restart, file edit, or package change. The only writes are sign-in session, add server, and remove server.

Show a visible **Read only** label on the monitoring pages.

## Screens

1. **Sign in** — username, password, submit.
2. **Server list** — saved servers, an add form (name, host), and remove on each row.
3. **Server detail** — summary tiles, charts, and the ports table. Link back to the list.

Layout for an operations reader: dark, high-contrast dashboard, large numbers, short labels, and charts under the matching tile. Empty list state asks the user to add a server. Tables stay usable on a laptop width.

## Tech

- Python 3 and Flask.
- Jinja templates, one CSS file, and a small script for refresh and charts.
- `psutil` for local CPU, memory, disk, network, and listening ports.
- `python-dotenv` to load `.env`.
- Chart.js from a CDN (no front-end build).
- Flask session cookie for sign-in.
- `data/servers.json` for the server list.

## Run locally

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask psutil python-dotenv
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('admin123'))"
```

Put the printed hash in `.env`:

```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<paste hash>
FLASK_SECRET_KEY=<any long random string>
```

```bash
flask --app app run --host 127.0.0.1 --port 5000
```

Open `http://127.0.0.1:5000` and sign in as `admin` / `admin123`.

## Out of scope

- Remote collection, SSH, agents, and other operating systems.
- Alerts, thresholds, tickets, and paging.
- More than one user, password change, and role-based access.
- History longer than the in-memory 5-minute window.
- Any change to the monitored machine.

## Acceptance

- Unsigned users see only the sign-in page.
- `admin` with the hashed password from `.env` reaches the server list. A wrong password does not.
- Adding a name and host shows that server on the list after refresh. A duplicate host is rejected. Remove deletes it after confirm.
- The detail page shows CPU, memory, disk, network, and listening ports from this machine, and the charts move after a few 5-second refreshes.
- The UI shows **Read only** and offers no host actions.
- Restarting the app keeps the server list and clears the charts.
