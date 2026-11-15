from contextlib import contextmanager
from dataclasses import dataclass

from tplinkrouterc6u import Connection, TplinkRouterProvider

from wifitracker.config import ROUTER_HOST, ROUTER_PASSWORD
from wifitracker.trust_store import normalize_mac


class BlockingNotSupported(Exception):
    """The router client has no block_device / unblock_device."""


@dataclass
class Device:
    mac: str
    hostname: str
    ip: str
    connection: str  # "2g" | "5g" | "6g" | "wired"
    active: bool = True


@contextmanager
def get_router():
    """Context manager — handles login and logout automatically."""
    client = TplinkRouterProvider.get_client(ROUTER_HOST, ROUTER_PASSWORD)
    client.authorize()
    try:
        yield client
    finally:
        client.logout()


def get_connected_devices(only_active: bool, router=None) -> list[Device]:
    if router is None:
        with get_router() as router:
            return get_connected_devices(only_active, router)

    status = router.get_status()
    devices = []
    for c in status.devices:
        if only_active and not c.active:
            continue
        devices.append(
            Device(
                mac=normalize_mac(c.macaddr),
                hostname=c.hostname or "unknown",
                ip=c.ipaddr or "",
                connection=_map_connection(c.type),
                active=c.active,
            )
        )
    return devices


def _require_blocking(router) -> None:
    if not (hasattr(router, "block_device") and hasattr(router, "unblock_device")):
        raise BlockingNotSupported(
            f"{type(router).__name__} cannot block devices (supported: Archer C24 / C80)"
        )


def block_device(mac: str, name: str = "", router=None) -> None:
    """Add the MAC to the router's Access Control blacklist."""
    if router is None:
        with get_router() as router:
            return block_device(mac, name, router)
    _require_blocking(router)
    router.block_device(normalize_mac(mac), name)


def unblock_device(mac: str, router=None) -> None:
    """Remove the MAC from the router's Access Control blacklist."""
    if router is None:
        with get_router() as router:
            return unblock_device(mac, router)
    _require_blocking(router)
    router.unblock_device(normalize_mac(mac))


def get_router_blocked(router=None) -> list[Device]:
    """Devices on the router's blacklist."""
    if router is None:
        with get_router() as router:
            return get_router_blocked(router)
    if not hasattr(router, "get_blocked_devices"):
        raise BlockingNotSupported(
            f"{type(router).__name__} cannot list blocked devices (supported: Archer C24 / C80)"
        )
    return [
        Device(mac=normalize_mac(d.macaddr), hostname=d.hostname, ip="", connection="", active=False)
        for d in router.get_blocked_devices()
    ]


def _map_connection(connection: Connection):
    return connection.value.split("_")[-1]
