"""Daily online-time limits.

A limit gives a device N hours of online time per day. The monitor adds the time
between scans to every active device; once a device uses up its hours it is blocked
on the router, and it is unblocked again when the day changes or the limit is raised
or removed.
"""
import json
from datetime import date
from pathlib import Path

from wifitracker.config import DATA_DIR, LIMITS_FILE, USAGE_FILE
from wifitracker.trust_store import normalize_mac


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save(path: Path, data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


# ── Limits ────────────────────────────────────────────────────────────────────


def get_limits() -> dict:
    return _load(LIMITS_FILE)


def set_limit(mac: str, hours: float, name: str = "") -> None:
    if hours < 0:
        raise ValueError("hours must be 0 or more")
    data = get_limits()
    data[normalize_mac(mac)] = {"hours": hours, "name": name}
    _save(LIMITS_FILE, data)


def remove_limit(mac: str) -> bool:
    data = get_limits()
    mac = normalize_mac(mac)
    if mac not in data:
        return False
    del data[mac]
    _save(LIMITS_FILE, data)
    return True


# ── Usage ─────────────────────────────────────────────────────────────────────


def get_usage(today: date | None = None) -> dict:
    """Today's usage: {"date", "seconds": {mac: float}, "blocked": [mac]}.

    On a new day the seconds start from zero, but "blocked" is kept so the monitor
    knows which devices it still has to unblock.
    """
    today_str = (today or date.today()).isoformat()
    usage = _load(USAGE_FILE)
    if usage.get("date") != today_str:
        usage = {"date": today_str, "seconds": {}, "blocked": usage.get("blocked", [])}
    usage.setdefault("seconds", {})
    usage.setdefault("blocked", [])
    return usage


def used_seconds(mac: str, today: date | None = None) -> float:
    return get_usage(today)["seconds"].get(normalize_mac(mac), 0.0)


def is_limit_blocked(mac: str) -> bool:
    return normalize_mac(mac) in get_usage()["blocked"]


def record_usage(active_macs: list[str], elapsed: float, today: date | None = None) -> tuple[list[str], list[str]]:
    """Add `elapsed` seconds to every active device that has a limit.

    Returns (to_block, to_unblock). Call mark_blocked / mark_unblocked once the router
    has actually done it, so a failed router call is retried on the next scan.
    """
    usage = get_usage(today)
    limits = get_limits()
    seconds = usage["seconds"]

    for mac in {normalize_mac(m) for m in active_macs}:
        if mac in limits and elapsed > 0:
            seconds[mac] = seconds.get(mac, 0.0) + elapsed

    def over_limit(mac: str) -> bool:
        return mac in limits and seconds.get(mac, 0.0) >= limits[mac]["hours"] * 3600

    to_block = [mac for mac in limits if over_limit(mac) and mac not in usage["blocked"]]
    to_unblock = [mac for mac in usage["blocked"] if not over_limit(mac)]
    _save(USAGE_FILE, usage)
    return to_block, to_unblock


def mark_blocked(mac: str, today: date | None = None) -> None:
    usage = get_usage(today)
    mac = normalize_mac(mac)
    if mac not in usage["blocked"]:
        usage["blocked"].append(mac)
    _save(USAGE_FILE, usage)


def mark_unblocked(mac: str, today: date | None = None) -> None:
    usage = get_usage(today)
    mac = normalize_mac(mac)
    usage["blocked"] = [m for m in usage["blocked"] if m != mac]
    _save(USAGE_FILE, usage)
