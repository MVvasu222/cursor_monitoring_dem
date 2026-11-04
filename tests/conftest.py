import os

import pytest
from werkzeug.security import generate_password_hash

if not os.environ.get("ADMIN_PASSWORD_HASH"):
    os.environ["ADMIN_PASSWORD_HASH"] = generate_password_hash("admin123")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key")


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    import metrics
    import servers

    monkeypatch.setattr(servers, "SERVERS_PATH", tmp_path / "servers.json")
    metrics.reset_state()
    yield
    metrics.reset_state()


@pytest.fixture
def client():
    from app import create_app

    return create_app(load_env=False).test_client()
