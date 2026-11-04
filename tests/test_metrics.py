import metrics


def _fake():
    return metrics.sample_from_parts(
        cpu_percent=12.5,
        load=[0.2, 0.4, 0.5],
        memory={"used": 1000, "free": 500, "percent": 66.0},
        disks=[{"mount": "/", "used": 20, "free": 80, "percent": 20.0}],
        interfaces=[{"name": "eth0", "bytes_in": 100, "bytes_out": 40}],
        bytes_in=100,
        bytes_out=40,
        ports=[{"port": 22, "protocol": "tcp", "address": "127.0.0.1", "process": "sshd"}],
    )


def test_fake_sample_uses_process_name_only():
    sample = _fake()
    assert sample["cpu_percent"] == 12.5
    assert sample["memory"]["free"] == 500
    assert sample["ports"][0]["process"] == "sshd"
    assert "cmdline" not in sample["ports"][0]


def test_history_stays_within_five_minutes():
    for index in range(70):
        result = metrics.record_sample(now=index * 5, collector=_fake)
    assert len(result["history"]) == metrics.HISTORY_LIMIT


def test_failed_read_keeps_previous_sample():
    calls = {"count": 0}

    def collector():
        calls["count"] += 1
        if calls["count"] > 1:
            raise RuntimeError("unavailable")
        return _fake()

    first = metrics.record_sample(now=0, collector=collector)
    second = metrics.record_sample(now=5, collector=collector)
    assert second["ok"] is False
    assert second["error"] == metrics.READ_ERROR
    assert second["sample"]["cpu_percent"] == first["sample"]["cpu_percent"]
    assert len(second["history"]) == 1
