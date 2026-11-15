import os
import signal
import sys
import time

from wifitracker.config import PID_FILE, SCAN_INTERVAL
from wifitracker.limits import get_limits, mark_blocked, mark_unblocked, record_usage
from wifitracker.notifier import (
    notify_error,
    notify_limit_blocked,
    notify_limit_unblocked,
    notify_unknown,
)
from wifitracker.router import block_device, get_connected_devices, get_router, unblock_device
from wifitracker.trust_store import add_blocked, is_blocked, is_trusted


def _scan_once(auto_block: bool, elapsed: float = 0.0) -> None:
    """One pass: alert on unknown devices, count online time, apply daily limits.

    `elapsed` is the time since the previous scan; it is added to the online time of
    every active device that has a limit.
    """
    with get_router() as router:
        devices = get_connected_devices(False, router)

        for device in devices:
            if is_trusted(device.mac) or is_blocked(device.mac):
                continue
            notify_unknown(device)
            if auto_block:
                block_device(device.mac, device.hostname, router)
                add_blocked(device.mac, reason="auto-blocked by monitor")

        _apply_limits(router, [d.mac for d in devices if d.active], elapsed)


def _apply_limits(router, active_macs: list[str], elapsed: float) -> None:
    to_block, to_unblock = record_usage(active_macs, elapsed)
    limits = get_limits()

    for mac in to_block:
        block_device(mac, limits[mac].get("name", ""), router)
        mark_blocked(mac)
        notify_limit_blocked(mac, limits[mac]["hours"])

    for mac in to_unblock:
        # A manual block outlives the limit: leave it on the router.
        if not is_blocked(mac):
            unblock_device(mac, router)
            notify_limit_unblocked(mac)
        mark_unblocked(mac)


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
        _run_loop(auto_block)
    except SystemExit:
        pass
    finally:
        PID_FILE.unlink(missing_ok=True)


def _run_loop(auto_block: bool) -> None:
    last_scan = None
    while True:
        now = time.monotonic()
        # Count at most a few missed intervals, so a laptop waking from sleep or a long
        # router outage does not charge hours of online time in one go.
        elapsed = 0.0 if last_scan is None else min(now - last_scan, SCAN_INTERVAL * 3)
        last_scan = now
        try:
            _scan_once(auto_block, elapsed)
        except Exception as e:  # keep the daemon alive through router/network errors
            notify_error(f"scan failed: {e}")
        time.sleep(SCAN_INTERVAL)


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
