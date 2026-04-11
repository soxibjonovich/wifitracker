import os
import json
from pathlib import Path


DATA_DIR: Path = Path.home() / ".wifitracker"
SETUP_FILE: Path = DATA_DIR / "setup.json"
BLOCKED_FILE: Path = DATA_DIR / "blocked_devices.json"
TRUSTED_FILE: Path = DATA_DIR / "trusted_devices.json"
PID_FILE: Path = Path("/tmp/archer_monitor.pid")

SCAN_INTERVAL: int = int(os.getenv("SCAN_INTERVAL", "30"))


def _load_setup() -> dict:
    if SETUP_FILE.exists():
        return json.loads(SETUP_FILE.read_text())
    return {}


_setup = _load_setup()

ROUTER_HOST: str = _setup.get("host") or os.getenv("ROUTER_HOST", "http://192.168.1.1")
ROUTER_PASSWORD: str = _setup.get("password") or os.getenv("ROUTER_PASSWORD", "admin")


def is_setup_done() -> bool:
    return SETUP_FILE.exists()
