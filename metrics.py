import socket
import threading
import time

import psutil

HISTORY_LIMIT = 60
SAMPLE_INTERVAL = 5
READ_ERROR = "Could not read this machine."

_lock = threading.Lock()
_history = []

# The first cpu_percent call only starts the clock. Prime it at import.
psutil.cpu_percent(interval=None)


def reset_state():
    with _lock:
        _history.clear()


def sample_from_parts(
    *,
    cpu_percent,
    load,
    memory,
    disks,
    interfaces,
    bytes_in,
    bytes_out,
    ports,
):
    return {
        "cpu_percent": cpu_percent,
        "load": list(load),
        "memory": {
            "used": memory["used"],
            "free": memory["free"],
            "percent": memory["percent"],
        },
        "disks": list(disks),
        "interfaces": list(interfaces),
        "bytes_in": bytes_in,
        "bytes_out": bytes_out,
        "ports": list(ports),
        "rate_in": 0.0,
        "rate_out": 0.0,
    }


def collect_sample():
    memory = psutil.virtual_memory()
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue
        disks.append(
            {
                "mount": part.mountpoint,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            }
        )

    interfaces = []
    bytes_in = 0
    bytes_out = 0
    for name, nic in psutil.net_io_counters(pernic=True).items():
        interfaces.append(
            {"name": name, "bytes_in": nic.bytes_recv, "bytes_out": nic.bytes_sent}
        )
        bytes_in += nic.bytes_recv
        bytes_out += nic.bytes_sent

    return sample_from_parts(
        cpu_percent=psutil.cpu_percent(interval=None),
        load=[round(value, 2) for value in psutil.getloadavg()],
        memory={"used": memory.used, "free": memory.available, "percent": memory.percent},
        disks=disks,
        interfaces=interfaces,
        bytes_in=bytes_in,
        bytes_out=bytes_out,
        ports=_listening_ports(),
    )


def record_sample(now=None, collector=None):
    if collector is None:
        collector = collect_sample
    if now is None:
        now = time.time()

    with _lock:
        if _history and now - _history[-1]["ts"] < SAMPLE_INTERVAL:
            return _payload(True, None, _history[-1])
        try:
            sample = collector()
        except Exception:
            if not _history:
                return _payload(False, READ_ERROR, None)
            return _payload(False, READ_ERROR, _history[-1])

        sample = dict(sample)
        previous = _history[-1] if _history else None
        sample["ts"] = now
        sample["rate_in"], sample["rate_out"] = _rates(previous, sample, now)
        _history.append(sample)
        del _history[:-HISTORY_LIMIT]
        return _payload(True, None, sample)


def _listening_ports():
    try:
        connections = psutil.net_connections(kind="inet")
    except (psutil.AccessDenied, PermissionError, OSError):
        return []

    ports = []
    for conn in connections:
        is_tcp = conn.type == socket.SOCK_STREAM
        is_udp = conn.type == socket.SOCK_DGRAM
        if is_tcp and conn.status != psutil.CONN_LISTEN:
            continue
        if not is_tcp and not is_udp:
            continue
        if not conn.laddr:
            continue
        process = ""
        if conn.pid:
            try:
                process = psutil.Process(conn.pid).name()
            except (psutil.Error, PermissionError, OSError):
                process = ""
        ports.append(
            {
                "port": conn.laddr.port,
                "protocol": "tcp" if is_tcp else "udp",
                "address": conn.laddr.ip,
                "process": process,
            }
        )
    ports.sort(key=lambda item: (item["port"], item["protocol"], item["address"]))
    return ports


def _rates(previous, sample, now):
    if previous is None:
        return 0.0, 0.0
    elapsed = now - previous["ts"]
    if elapsed <= 0:
        return 0.0, 0.0
    return (
        max(0.0, (sample["bytes_in"] - previous["bytes_in"]) / elapsed),
        max(0.0, (sample["bytes_out"] - previous["bytes_out"]) / elapsed),
    )


def _payload(ok, error, sample):
    return {
        "ok": ok,
        "error": error,
        "sample": sample,
        "history": [dict(item) for item in _history],
    }
