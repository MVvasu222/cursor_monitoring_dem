import servers


def _login(client):
    response = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 302


def _csrf(html):
    marker = b'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    end = html.index(b'"', start)
    return html[start:end].decode()


def test_add_shows_row_duplicate_errors_remove_drops_row(client):
    _login(client)
    page = client.get("/")
    token = _csrf(page.data)
    added = client.post(
        "/servers",
        data={"csrf_token": token, "name": "Edge <box>", "host": "10.1.1.5"},
        follow_redirects=True,
    )
    assert added.status_code == 200
    assert b"Edge &lt;box&gt;" in added.data
    assert b"10.1.1.5" in added.data

    token = _csrf(added.data)
    duplicate = client.post(
        "/servers",
        data={"csrf_token": token, "name": "Copy", "host": "10.1.1.5"},
    )
    assert duplicate.status_code == 400
    assert b"That host is already in the list." in duplicate.data

    token = _csrf(duplicate.data)
    server_id = servers.list_servers()[0]["id"]
    removed = client.post(
        f"/servers/{server_id}/delete",
        data={"csrf_token": token, "confirm": "yes"},
        follow_redirects=True,
    )
    assert removed.status_code == 200
    assert b"10.1.1.5" not in removed.data
    assert b"Add a server to begin." in removed.data


def test_remove_without_confirm_keeps_the_row(client):
    _login(client)
    token = _csrf(client.get("/").data)
    client.post("/servers", data={"csrf_token": token, "name": "Edge", "host": "10.1.1.8"})
    token = _csrf(client.get("/").data)
    server_id = servers.list_servers()[0]["id"]
    denied = client.post(f"/servers/{server_id}/delete", data={"csrf_token": token})
    assert denied.status_code == 400
    assert servers.list_servers()[0]["host"] == "10.1.1.8"


def test_detail_is_read_only(client, monkeypatch):
    import metrics

    monkeypatch.setattr(metrics, "collect_sample", lambda: _sample())
    _login(client)
    record = servers.add_server("Edge", "127.0.0.1")
    page = client.get(f"/servers/{record['id']}")
    assert page.status_code == 200
    assert b"Read only" in page.data
    assert b"sshd" in page.data
    assert b"Kill" not in page.data
    assert b"Restart" not in page.data


def test_sample_requires_sign_in_and_returns_saved_server(client, monkeypatch):
    import metrics

    monkeypatch.setattr(metrics, "collect_sample", lambda: _sample())
    blocked = client.get("/servers/missing/sample")
    assert blocked.status_code == 302
    assert blocked.headers["Location"].endswith("/login")

    _login(client)
    record = servers.add_server("Edge", "127.0.0.1")
    payload = client.get(f"/servers/{record['id']}/sample").get_json()
    assert payload["ok"] is True
    assert payload["sample"]["ports"][0]["process"] == "sshd"
    missing = client.get("/servers/not-a-saved-id/sample")
    assert missing.status_code == 404


def _sample():
    import metrics

    return metrics.sample_from_parts(
        cpu_percent=3,
        load=[0.1, 0.1, 0.1],
        memory={"used": 10, "free": 90, "percent": 10},
        disks=[{"mount": "/", "used": 1, "free": 1, "percent": 50}],
        interfaces=[{"name": "lo", "bytes_in": 1, "bytes_out": 1}],
        bytes_in=1,
        bytes_out=1,
        ports=[{"port": 22, "protocol": "tcp", "address": "127.0.0.1", "process": "sshd"}],
    )
