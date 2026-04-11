import pytest
from unittest.mock import patch
from wifitracker.router import Device


@pytest.fixture
def unknown_device():
    return Device(
        mac="AA:BB:CC:DD:EE:FF",
        hostname="stranger",
        ip="192.168.1.99",
        connection="2.4GHz",
    )


def test_scan_notifies_unknown(unknown_device):
    with (
        patch("wifitracker.monitor.get_connected_devices", return_value=[unknown_device]),
        patch("wifitracker.monitor.is_trusted", return_value=False),
        patch("wifitracker.monitor.notify_unknown") as mock_notify,
        patch("wifitracker.monitor.add_blocked") as mock_block,
    ):
        from wifitracker.monitor import _scan_once
        _scan_once(auto_block=False)

        mock_notify.assert_called_once_with(unknown_device)
        mock_block.assert_not_called()


def test_scan_auto_blocks_unknown(unknown_device):
    with (
        patch("wifitracker.monitor.get_connected_devices", return_value=[unknown_device]),
        patch("wifitracker.monitor.is_trusted", return_value=False),
        patch("wifitracker.monitor.notify_unknown"),
        patch("wifitracker.monitor.add_blocked") as mock_block,
    ):
        from wifitracker.monitor import _scan_once
        _scan_once(auto_block=True)

        mock_block.assert_called_once_with(unknown_device.mac, reason="auto-blocked by monitor")


def test_scan_skips_trusted_device():
    trusted = Device(mac="AA:BB:CC:DD:EE:FF", hostname="phone", ip="192.168.1.10", connection="5GHz")
    with (
        patch("wifitracker.monitor.get_connected_devices", return_value=[trusted]),
        patch("wifitracker.monitor.is_trusted", return_value=True),
        patch("wifitracker.monitor.notify_unknown") as mock_notify,
    ):
        from wifitracker.monitor import _scan_once
        _scan_once(auto_block=True)

        mock_notify.assert_not_called()
