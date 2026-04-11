from wifitracker.router import _map_connection
from tplinkrouterc6u import Connection


def test_map_2g():
    assert _map_connection(Connection.HOST_2G) == "2g"


def test_map_5g():
    assert _map_connection(Connection.HOST_5G) == "5g"
