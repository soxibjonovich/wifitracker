import json
import re
from datetime import datetime
from pathlib import Path

from wifitracker.config import BLOCKED_FILE, TRUSTED_FILE, DATA_DIR


def normalize_mac(mac: str) -> str:
    """Return the MAC as AA:BB:CC:DD:EE:FF, whatever separator it came with."""
    digits = re.sub(r"[^0-9A-Fa-f]", "", mac).upper()
    if len(digits) != 12:
        raise ValueError(f"Invalid MAC address: {mac}")
    return ":".join(digits[i:i + 2] for i in range(0, 12, 2))


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    # Older files may hold keys like AA-BB-...; bring them to one format.
    normalized = {}
    for key, value in data.items():
        try:
            normalized[normalize_mac(key)] = value
        except ValueError:
            normalized[key] = value
    return normalized


def _save(path: Path, data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


# ── Trusted ───────────────────────────────────────────────────────────────────


def get_trusted() -> dict:
    return _load(TRUSTED_FILE)


def add_trusted(mac: str, name: str = "") -> None:
    data = get_trusted()
    data[normalize_mac(mac)] = {"name": name, "added": datetime.now().isoformat()}
    _save(TRUSTED_FILE, data)


def remove_trusted(mac: str) -> bool:
    data = get_trusted()
    if normalize_mac(mac) not in data:
        return False
    del data[normalize_mac(mac)]
    _save(TRUSTED_FILE, data)
    return True


def is_trusted(mac: str) -> bool:
    return normalize_mac(mac) in get_trusted()


# ── Blocked ───────────────────────────────────────────────────────────────────


def get_blocked() -> dict:
    return _load(BLOCKED_FILE)


def add_blocked(mac: str, reason: str = "untrusted") -> None:
    data = get_blocked()
    data[normalize_mac(mac)] = {
        "reason": reason,
        "blocked_at": datetime.now().isoformat(),
    }
    _save(BLOCKED_FILE, data)


def remove_blocked(mac: str) -> bool:
    data = get_blocked()
    if normalize_mac(mac) not in data:
        return False
    del data[normalize_mac(mac)]
    _save(BLOCKED_FILE, data)
    return True


def is_blocked(mac: str) -> bool:
    return normalize_mac(mac) in get_blocked()
