import pytest

import servers


def test_add_duplicate_remove_and_reload(tmp_path):
    path = tmp_path / "servers.json"
    servers.add_server("Web", "10.0.0.8", path)
    servers.add_server("DB", "db.internal", path)
    with pytest.raises(servers.StoreError, match="already"):
        servers.add_server("Other", "10.0.0.8", path)
    loaded = servers.list_servers(path)
    assert [item["name"] for item in loaded] == ["Web", "DB"]
    servers.remove_server(loaded[0]["id"], path)
    assert [item["host"] for item in servers.list_servers(path)] == ["db.internal"]


def test_rejects_blank_long_and_bad_host(tmp_path):
    path = tmp_path / "servers.json"
    with pytest.raises(servers.StoreError):
        servers.add_server(" ", "localhost", path)
    with pytest.raises(servers.StoreError):
        servers.add_server("n" * 81, "localhost", path)
    with pytest.raises(servers.StoreError):
        servers.add_server("ok", "not a host", path)
    with pytest.raises(servers.StoreError):
        servers.add_server("ok", "h" * 254, path)
