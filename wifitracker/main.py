import typer
import json
from rich.console import Console
from rich.table import Table
from tplinkrouterc6u import ClientException

from wifitracker.config import is_setup_done, DATA_DIR, SETUP_FILE
from wifitracker import monitor
from wifitracker.limits import (
    get_limits,
    get_usage,
    is_limit_blocked,
    mark_unblocked,
    remove_limit,
    set_limit,
)
from wifitracker.trust_store import (
    add_blocked,
    add_trusted,
    get_blocked,
    get_trusted,
    normalize_mac,
    remove_blocked,
    remove_trusted,
)

from wifitracker.router import (
    BlockingNotSupported,
    block_device,
    get_connected_devices,
    get_router_blocked,
    unblock_device,
)

app = typer.Typer(help="Wifi router CLI manager")
devices_app = typer.Typer(help="Manage connected devices")
monitor_app = typer.Typer(help="Background monitor daemon")
wifi_app = typer.Typer(help="Control WiFi bands")

app.add_typer(devices_app, name="devices")
app.add_typer(monitor_app, name="monitor")
app.add_typer(wifi_app, name="wifi")

console = Console()


def _require_setup() -> None:
    if not is_setup_done():
        console.print("[red]Run 'wifitracker setup' first.[/red]")
        raise typer.Exit(1)


def _mac_arg(mac: str) -> str:
    try:
        return normalize_mac(mac)
    except ValueError as e:
        raise typer.BadParameter(str(e))


def _router_call(fn, *args) -> None:
    """Run a router action; print the error and exit 1 if it fails."""
    try:
        fn(*args)
    except (BlockingNotSupported, ClientException) as e:
        console.print(f"[red]Router error:[/red] {e}")
        raise typer.Exit(1)


def _format_hours(seconds: float) -> str:
    return f"{seconds / 3600:.1f}h"


@app.command()
def setup(
    host: str = typer.Option("http://192.168.1.1", "--host"),
    password: str = typer.Option(..., "--password", prompt=True, hide_input=True),
):
    """Configure router credentials."""
    if is_setup_done():
        console.print("[red]You have already set up[/red]")
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETUP_FILE.write_text(json.dumps({"host": host, "password": password}, indent=2))
    console.print("[green]Setup complete![/green]")


#  ------ devices ------
@devices_app.command("list")
def list_devices(
    only_active: bool = typer.Option(False, help="filter only active devices"),
):
    _require_setup()
    devices = get_connected_devices(only_active)
    trusted = get_trusted()
    blocked = get_blocked()
    limits = get_limits()
    usage = get_usage()

    table = Table(title="Connected Devices")
    table.add_column("Hostname", style="cyan")
    table.add_column("MAC")
    table.add_column("IP")
    table.add_column("Band")
    table.add_column("Status")
    table.add_column("Today")
    for d in devices:
        mac = d.mac
        if mac in blocked:
            status = "[red]BLOCKED[/red]"
        elif mac in usage["blocked"]:
            status = "[red]LIMIT REACHED[/red]"
        elif mac in trusted:
            status = "[green]trusted[/green]"
        else:
            status = "[yellow]unknown[/yellow]"
        today = _format_hours(usage["seconds"].get(mac, 0.0))
        if mac in limits:
            today += f" / {limits[mac]['hours']:g}h"
        table.add_row(d.hostname, mac, d.ip, d.connection, status, today)

    console.print(table)


@devices_app.command("trust")
def devices_trust(mac: str = typer.Argument(..., callback=_mac_arg), name: str = ""):
    """Add a device MAC to the trusted list"""
    add_trusted(mac, name)
    console.print(f"[green]Trusted:[/green] {mac}")


@devices_app.command("untrust")
def devices_untrust(mac: str = typer.Argument(..., callback=_mac_arg)):
    """Remove a device from the trusted list."""
    if remove_trusted(mac):
        console.print(f"[yellow]Removed trust:[/yellow] {mac}")
    else:
        console.print(f"[red]Not found in trusted list:[/red] {mac}")


@devices_app.command("block")
def devices_block(
    mac: str = typer.Argument(..., callback=_mac_arg),
    name: str = typer.Option("", help="name stored on the router (default: the MAC)"),
):
    """Block a device on the router (Access Control blacklist)."""
    _require_setup()
    _router_call(block_device, mac, name)
    add_blocked(mac, reason="manual block")
    console.print(f"[red]Blocked:[/red] {mac}")


@devices_app.command("unblock")
def devices_unblock(mac: str = typer.Argument(..., callback=_mac_arg)):
    """Unblock a device on the router."""
    _require_setup()
    _router_call(unblock_device, mac)
    remove_blocked(mac)
    if is_limit_blocked(mac):
        # Unblocked by hand: let it back on for the rest of the day.
        mark_unblocked(mac)
        console.print("[yellow]Note:[/yellow] its daily limit is still set; it is blocked again tomorrow once used up")
    console.print(f"[green]Unblocked:[/green] {mac}")


@devices_app.command("blocked")
def devices_blocked():
    """Show the devices blocked on the router."""
    _require_setup()
    try:
        devices = get_router_blocked()
    except (BlockingNotSupported, ClientException) as e:
        console.print(f"[red]Router error:[/red] {e}")
        raise typer.Exit(1)
    table = Table(title=f"Blocked on router ({len(devices)})")
    table.add_column("MAC")
    table.add_column("Name", style="cyan")
    for d in devices:
        table.add_row(d.mac, d.hostname)
    console.print(table)


@devices_app.command("limit")
def devices_limit(
    mac: str = typer.Argument(..., callback=_mac_arg),
    hours: float = typer.Argument(..., min=0, help="online hours allowed per day"),
    name: str = typer.Option("", help="label for the device"),
):
    """Allow a device N hours online per day; the monitor blocks it after that."""
    set_limit(mac, hours, name)
    console.print(f"[green]Limit set:[/green] {mac} {hours:g}h per day")
    console.print("Online time is counted by the monitor: run 'wifitracker monitor start'.")


@devices_app.command("unlimit")
def devices_unlimit(mac: str = typer.Argument(..., callback=_mac_arg)):
    """Remove a device's daily limit (the monitor unblocks it on its next scan)."""
    if remove_limit(mac):
        console.print(f"[green]Limit removed:[/green] {mac}")
    else:
        console.print(f"[red]No limit set for:[/red] {mac}")


@devices_app.command("limits")
def devices_limits():
    """Show daily limits and today's online time."""
    limits = get_limits()
    usage = get_usage()
    table = Table(title=f"Daily limits ({usage['date']})")
    table.add_column("MAC")
    table.add_column("Name", style="cyan")
    table.add_column("Used today")
    table.add_column("Limit")
    table.add_column("Status")
    for mac, limit in limits.items():
        status = "[red]LIMIT REACHED[/red]" if mac in usage["blocked"] else "[green]allowed[/green]"
        table.add_row(
            mac,
            limit.get("name", ""),
            _format_hours(usage["seconds"].get(mac, 0.0)),
            f"{limit['hours']:g}h",
            status,
        )
    console.print(table)


# ── Monitor ───────────────────────────────────────────────────────────────────


@monitor_app.command("start")
def monitor_start(
    auto_block: bool = typer.Option(
        False, "--auto-block", help="Auto-block unknown devices"
    ),
):
    """Start the background monitor daemon."""
    monitor.start_monitor(auto_block=auto_block)


@monitor_app.command("stop")
def monitor_stop():
    """Stop the background monitor daemon."""
    monitor.stop_monitor()


@monitor_app.command("status")
def monitor_status():
    """Check if the monitor is running."""
    monitor.monitor_status()
