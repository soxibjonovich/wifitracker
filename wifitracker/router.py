from contextlib import contextmanager
from dataclasses import dataclass

from tplinkrouterc6u import Connection, TplinkRouterProvider

from wifitracker.config import ROUTER_HOST, ROUTER_PASSWORD


@dataclass
class Device:
    mac: str
    hostname: str
    ip: str
    connection: str  # "2.5GHz" | "5GHz" | "wired"


@contextmanager
def get_router():
    """Context manager — handles login and logout automatically."""
    client = TplinkRouterProvider.get_client(ROUTER_HOST, ROUTER_PASSWORD)
    client.authorize()
    try:
        yield client
    finally:
        client.logout()


def get_connected_devices(only_active: bool) -> list[Device]:
    with get_router() as router:
        status = router.get_status()
        devices = []
        for c in status.devices:
            if only_active and not c.active:
                continue
            devices.append(
                Device(
                    mac=c.macaddr.upper(),
                    hostname=c.hostname or "unknown",
                    ip=c.ipaddr or "",
                    connection=_map_connection(c.type),
                )
            )
        return devices


def _map_connection(connection: Connection):
    return connection.value.split("_")[-1]
