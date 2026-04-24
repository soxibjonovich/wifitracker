import json
from datetime import datetime
from pathlib import Path

from wifitracker.config import BLOCKED_FILE, TRUSTED_FILE, DATA_DIR


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save(path: Path, data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


# ── Trusted ───────────────────────────────────────────────────────────────────


def get_trusted() -> dict:
    return _load(TRUSTED_FILE)


def add_trusted(mac: str, name: str = "") -> None:
    data = get_trusted()
    data[mac.upper()] = {"name": name, "added": datetime.now().isoformat()}
    _save(TRUSTED_FILE, data)


def remove_trusted(mac: str) -> bool:
    data = get_trusted()
    if mac.upper() not in data:
        return False
    del data[mac.upper()]
    _save(TRUSTED_FILE, data)
    return True


def is_trusted(mac: str) -> bool:
    return mac.upper() in get_trusted()


# ── Blocked ───────────────────────────────────────────────────────────────────


def get_blocked() -> dict:
    return _load(BLOCKED_FILE)


def add_blocked(mac: str, reason: str = "untrusted") -> None:
    data = get_blocked()
    data[mac.upper()] = {
        "reason": reason,
        "blocked_at": datetime.now().isoformat(),
    }
    _save(BLOCKED_FILE, data)


def remove_blocked(mac: str) -> bool:
    data = get_blocked()
    if mac.upper() not in data:
        return False
    del data[mac.upper()]
    _save(BLOCKED_FILE, data)
    return True


def is_blocked(mac: str) -> bool:
    return mac.upper() in get_blocked()
