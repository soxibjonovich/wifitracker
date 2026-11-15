from wifitracker.router import _map_connection
from tplinkrouterc6u import Connection


def test_map_2g():
    assert _map_connection(Connection.HOST_2G) == "2g"


def test_map_5g():
    assert _map_connection(Connection.HOST_5G) == "5g"


from unittest.mock import MagicMock

import pytest

from wifitracker import router as router_module


def test_block_device_normalizes_mac():
    client = MagicMock()
    router_module.block_device("aa-bb-cc-dd-ee-ff", "kid", client)
    client.block_device.assert_called_once_with("AA:BB:CC:DD:EE:FF", "kid")


def test_unblock_device_normalizes_mac():
    client = MagicMock()
    router_module.unblock_device("aabbccddeeff", client)
    client.unblock_device.assert_called_once_with("AA:BB:CC:DD:EE:FF")


def test_router_without_blocking_raises():
    client = MagicMock(spec=["get_status"])
    with pytest.raises(router_module.BlockingNotSupported):
        router_module.block_device("AA:BB:CC:DD:EE:FF", "", client)


def test_get_router_blocked():
    blocked = MagicMock(macaddr="AA-BB-CC-DD-EE-FF", hostname="kid")
    client = MagicMock()
    client.get_blocked_devices.return_value = [blocked]
    devices = router_module.get_router_blocked(client)
    assert [(d.mac, d.hostname) for d in devices] == [("AA:BB:CC:DD:EE:FF", "kid")]
