# Server Monitor

Local demo for reading Linux server stats. Product requirements: [docs/requirements.md](docs/requirements.md).

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/flask --app app run --host 127.0.0.1 --port 5000
```

Open http://127.0.0.1:5000.
