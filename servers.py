import ipaddress
import json
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERVERS_PATH = ROOT / "data" / "servers.json"
MAX_NAME = 80
MAX_HOST = 253

_HOSTNAME = re.compile(
    r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)"
    r"(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*$"
)


class StoreError(Exception):
    pass


def list_servers(path=None):
    path = _path(path)
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8").strip() or "[]"
    data = json.loads(raw)
    if not isinstance(data, list):
        raise StoreError("Server list is unreadable.")
    return data


def add_server(name, host, path=None):
    path = _path(path)
    name = (name or "").strip()
    host = (host or "").strip()
    if not name or not host or len(name) > MAX_NAME or not _valid_host(host):
        raise StoreError("Enter a display name and a hostname or IPv4 address.")
    items = list_servers(path)
    if any(item["host"].lower() == host.lower() for item in items):
        raise StoreError("That host is already in the list.")
    record = {"id": uuid.uuid4().hex, "name": name, "host": host}
    items.append(record)
    _write(items, path)
    return record


def remove_server(server_id, path=None):
    path = _path(path)
    items = list_servers(path)
    kept = [item for item in items if item["id"] != server_id]
    if len(kept) == len(items):
        raise StoreError("Server not found.")
    _write(kept, path)


def find_server(server_id, path=None):
    for item in list_servers(path):
        if item["id"] == server_id:
            return item
    return None


def _path(path):
    return Path(path) if path is not None else SERVERS_PATH


def _write(items, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _valid_host(host):
    if len(host) > MAX_HOST:
        return False
    try:
        ipaddress.IPv4Address(host)
        return True
    except ipaddress.AddressValueError:
        return _HOSTNAME.fullmatch(host) is not None
