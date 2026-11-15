from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from wifitracker import limits, monitor, trust_store
from wifitracker.router import Device

MAC = "AA:BB:CC:DD:EE:FF"


@pytest.fixture
def router():
    client = MagicMock()

    @contextmanager
    def fake_get_router():
        yield client

    with patch("wifitracker.monitor.get_router", fake_get_router):
        yield client


@pytest.fixture
def unknown_device():
    return Device(mac=MAC, hostname="stranger", ip="192.168.1.99", connection="2g")


def _devices(*devices):
    return patch("wifitracker.monitor.get_connected_devices", return_value=list(devices))


def test_scan_notifies_unknown(router, unknown_device):
    with _devices(unknown_device), patch("wifitracker.monitor.notify_unknown") as mock_notify:
        monitor._scan_once(auto_block=False)

    mock_notify.assert_called_once_with(unknown_device)
    router.block_device.assert_not_called()


def test_scan_auto_blocks_unknown_on_router(router, unknown_device):
    with _devices(unknown_device), patch("wifitracker.monitor.notify_unknown"):
        monitor._scan_once(auto_block=True)

    router.block_device.assert_called_once_with(MAC, "stranger")
    assert trust_store.get_blocked()[MAC]["reason"] == "auto-blocked by monitor"


def test_scan_skips_trusted_device(router):
    trust_store.add_trusted(MAC)
    trusted = Device(mac=MAC, hostname="phone", ip="192.168.1.10", connection="5g")
    with _devices(trusted), patch("wifitracker.monitor.notify_unknown") as mock_notify:
        monitor._scan_once(auto_block=True)

    mock_notify.assert_not_called()
    router.block_device.assert_not_called()


def test_scan_blocks_device_over_daily_limit(router):
    trust_store.add_trusted(MAC)
    limits.set_limit(MAC, 1, "tablet")
    tablet = Device(mac=MAC, hostname="tablet", ip="192.168.1.11", connection="5g")
    with _devices(tablet):
        monitor._scan_once(auto_block=False, elapsed=3000)
        router.block_device.assert_not_called()
        monitor._scan_once(auto_block=False, elapsed=600)

    router.block_device.assert_called_once_with(MAC, "tablet")
    assert limits.is_limit_blocked(MAC)


def test_inactive_device_time_not_counted(router):
    trust_store.add_trusted(MAC)
    limits.set_limit(MAC, 1)
    idle = Device(mac=MAC, hostname="tablet", ip="", connection="5g", active=False)
    with _devices(idle):
        monitor._scan_once(auto_block=False, elapsed=7200)

    router.block_device.assert_not_called()


def test_failed_router_block_retried_next_scan(router):
    trust_store.add_trusted(MAC)
    limits.set_limit(MAC, 0)
    router.block_device.side_effect = [RuntimeError("router down"), None]
    with _devices():
        with pytest.raises(RuntimeError):
            monitor._scan_once(auto_block=False)
        monitor._scan_once(auto_block=False)

    assert router.block_device.call_count == 2
    assert limits.is_limit_blocked(MAC)


def test_limit_unblock_keeps_manual_block(router):
    limits.set_limit(MAC, 1)
    limits.mark_blocked(MAC)
    trust_store.add_blocked(MAC, reason="manual block")
    limits.remove_limit(MAC)
    with _devices():
        monitor._scan_once(auto_block=False)

    router.unblock_device.assert_not_called()
    assert not limits.is_limit_blocked(MAC)


def test_limit_unblock_calls_router(router):
    limits.set_limit(MAC, 1)
    limits.mark_blocked(MAC)
    limits.remove_limit(MAC)
    with _devices():
        monitor._scan_once(auto_block=False)

    router.unblock_device.assert_called_once_with(MAC)
