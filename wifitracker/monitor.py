import os
import signal
import sys
import time

from wifitracker.config import PID_FILE, SCAN_INTERVAL
from wifitracker.notifier import notify_unknown
from wifitracker.router import get_connected_devices
from wifitracker.trust_store import add_blocked, is_trusted


def _scan_once(auto_block: bool) -> None:
    devices = get_connected_devices(False)
    for device in devices:
        if not is_trusted(device.mac):
            notify_unknown(device)
            if auto_block:
                add_blocked(device.mac, reason="auto-blocked by monitor")


def start_monitor(auto_block: bool = False) -> None:
    """Fork a background process and save PID."""
    if PID_FILE.exists():
        print("Monitor is already running. Use 'monitor stop' first.")
        return

    pid = os.fork()

    if pid > 0:
        # Parent process — write PID and return terminal to user
        PID_FILE.write_text(str(pid))
        print(f"Monitor started (PID {pid})")
        sys.exit(0)

    # Child process — run forever
    signal.signal(signal.SIGTERM, _handle_sigterm)
    try:
        while True:
            _scan_once(auto_block)
            time.sleep(SCAN_INTERVAL)
    except SystemExit:
        pass
    finally:
        PID_FILE.unlink(missing_ok=True)


def stop_monitor() -> None:
    if not PID_FILE.exists():
        print("Monitor is not running.")
        return
    pid = int(PID_FILE.read_text())
    os.kill(pid, signal.SIGTERM)
    PID_FILE.unlink(missing_ok=True)
    print(f"Monitor stopped (PID {pid})")


def monitor_status() -> None:
    if PID_FILE.exists():
        pid = PID_FILE.read_text().strip()
        print(f"Monitor is running — PID {pid}")
    else:
        print("Monitor is not running.")


def _handle_sigterm(signum, frame) -> None:
    sys.exit(0)
