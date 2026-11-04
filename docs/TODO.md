# Implementation TODO

Work top to bottom. Finish one section before the next. Each section is one small change: code, a security check, and a doc update.

Local demo only. Bind the app to `127.0.0.1`. Do not add SSH, agents, or host controls.

## 1. Project initialization and basic UI

- [x] Add `app.py`, `requirements.txt` (`flask`, `psutil`, `python-dotenv`), and `.gitignore` (`.venv/`, `.env`, `__pycache__/`).
- [x] Add a dark page shell: header, short title, and an empty main area. No data yet.
- [x] Serve it at `http://127.0.0.1:5000` with `flask --app app run --host 127.0.0.1 --port 5000`.
- [x] Security: bind to localhost only. Do not put passwords, hashes, or secret keys in code or templates.
- [x] Docs: add `README.md` with the three commands to create the venv, install, and run. Link `docs/requirements.md`.

## 2. Sign-in and unit tests

- [x] Add `.env.example` with `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, and `FLASK_SECRET_KEY`.
- [x] Load `.env` at startup. Compare the password with Werkzeug `check_password_hash`. Demo password is `admin123`; store only the hash.
- [x] Add a sign-in page, a sign-out action, and a session flag. Wrong credentials stay on the sign-in page with a short error.
- [x] Send every other route to sign-in when the session is missing.
- [x] Add `pytest` and tests: valid login, wrong password, unsigned redirect, sign-out. Tests set env vars themselves and do not read a real `.env`.
- [x] Security: session cookie `HttpOnly` and `SameSite=Lax`. Regenerate the session on sign-in. Use one generic error line. Do not log the password.
- [x] Docs: README section for generating the hash and filling `.env`. Note that `.env` stays untracked.

## 3. GitHub Actions

- [x] Add `.github/workflows/test.yml`. On push and pull request: Python 3.11, install `requirements.txt` and `pytest`, run `pytest`.
- [x] Pass test env vars in the workflow (`ADMIN_USERNAME`, a Werkzeug hash of `admin123`, `FLASK_SECRET_KEY`). No repository secrets.
- [x] Security: the workflow does not print `.env` or deploy anywhere. Dependencies come only from `requirements.txt`.
- [x] Docs: README line that tests run in GitHub Actions and locally with `pytest`.

## 4. Server list storage

- [x] Add `data/servers.json` (start as `[]`) and a helper to load and save `{name, host}` records.
- [x] Require both fields. Accept a hostname or an IPv4 address. Reject a duplicate host.
- [x] Unit test add, duplicate rejection, remove, and a restart-style reload from the JSON file. Use a temp file, not the repo copy.
- [x] Security: fixed path under `data/`. No shell calls. Trim length (name ≤ 80, host ≤ 253).
- [x] Docs: one README sentence that the server list is `data/servers.json`.

## 5. Add and remove servers in the UI

- [x] Server list page: saved rows (name, host), an add form, and a remove button with a confirm step.
- [x] Empty state text: add a server to begin.
- [x] After add or remove, show the updated list.
- [x] Tests: add shows the row, duplicate host returns an error, remove drops the row.
- [x] Security: POST only for add and remove. Same-origin form with a session CSRF token. Escape name and host in the template.
- [x] Docs: README note for the add form and confirm-before-remove.

## 6. Read-only monitoring shell

- [x] Server detail page with the server name, host, a **Read only** label, and a link back to the list. Placeholder tiles only.
- [x] Security: page is view-only. No buttons that change the host.
- [x] Docs: README line that the detail view cannot change the machine.

## 7. Local metrics snapshot

- [x] Add a collector with `psutil` for one sample: CPU percent and load average; memory used, free, percent; each mount used, free, percent; per-interface bytes in and out; listening ports (port, protocol, address, process name).
- [x] Render that sample on the detail page.
- [x] Unit test the collector with a fake sample so tests do not depend on live host numbers.
- [x] Security: process name only. No command lines, no shell, no writes to the host.
- [x] Docs: README list of the five metric areas and the local-machine data rule.

## 8. Five-second refresh and charts

- [x] Add a session-protected JSON route that returns the latest sample for a saved server id.
- [x] Keep about 5 minutes of samples in memory (one point per 5 seconds). Restart clears this history.
- [x] Poll every 5 seconds and update the tiles in place. Chart.js from a pinned CDN: CPU percent, memory percent, root (`/`) disk percent, total send and receive rate.
- [x] On a failed sample, show a short error and leave the last good numbers and charts on screen.
- [x] Tests: JSON requires sign-in; history length stays within the 5-minute cap; a failed read keeps the previous sample.
- [x] Security: JSON only for a signed-in session. Server id is the saved record, not a path or shell argument. Pin the Chart.js version.
- [x] Docs: README note for the 5-second refresh, the 5-minute memory window, and that a restart clears charts only.

## 9. Acceptance pass

- [x] Walk `docs/requirements.md` acceptance items once on `http://127.0.0.1:5000`.
- [x] Security: confirm `.env` is untracked, the app listens on `127.0.0.1` only, and the UI has no host actions.
- [x] Docs: check the run steps in `README.md` against the commands you just used.
