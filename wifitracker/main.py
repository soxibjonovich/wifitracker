import typer
import json
from rich.console import Console
from rich.table import Table
from wifitracker.config import is_setup_done, DATA_DIR, SETUP_FILE
from wifitracker import monitor
from wifitracker.trust_store import (
    add_blocked,
    add_trusted,
    get_blocked,
    get_trusted,
    remove_blocked,
    remove_trusted,
)

from wifitracker.router import get_connected_devices

app = typer.Typer(help="Wifi router CLI manager")
devices_app = typer.Typer(help="Manage connected devices")
monitor_app = typer.Typer(help="Background monitor daemon")
wifi_app = typer.Typer(help="Control WiFi bands")

app.add_typer(devices_app, name="devices")
app.add_typer(monitor_app, name="monitor")
app.add_typer(wifi_app, name="wifi")

console = Console()


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
    if not is_setup_done():
        console.print("[red]Run 'wifitracker setup' first.[/red]")
        raise typer.Exit(1)
    devices = get_connected_devices(only_active)
    trusted = get_trusted()
    blocked = get_blocked()

    table = Table(title="Connected Devices")
    table.add_column("Hostname", style="cyan")
    table.add_column("MAC")
    table.add_column("IP")
    table.add_column("Band")
    table.add_column("Status")
    for d in devices:
        mac = d.mac.upper().replace("-", ":").replace(".", ":")
        if mac in blocked:
            status = "[red]BLOCKED[/red]"
        elif mac in trusted:
            status = "[green]trusted[/green]"
        else:
            status = "[yellow]unknown[/yellow]"
        table.add_row(d.hostname, mac, d.ip, d.connection, status)

    console.print(table)


@devices_app.command("trust")
def devices_trust(mac: str, name: str = ""):
    """Add a device MAC to the trusted list"""
    add_trusted(mac, name)
    console.print(f"[green]Trusted:[/green] {mac}")


@devices_app.command("untrust")
def devices_untrust(mac: str):
    """Remove a device from the trusted list."""
    if remove_trusted(mac):
        console.print(f"[yellow]Removed trust:[/yellow] {mac}")
    else:
        console.print(f"[red]Not found in trusted list:[/red] {mac}")


@devices_app.command("block")
def devices_block(mac: str):
    """Block a device by MAC address."""
    add_blocked(mac, reason="manual block")
    console.print(f"[red]Blocked:[/red] {mac}")


@devices_app.command("unblock")
def devices_unblock(mac: str):
    """Remove a device from the block list."""
    if remove_blocked(mac):
        console.print(f"[green]Unblocked:[/green] {mac}")
    else:
        console.print(f"[red]Not found in blocked list:[/red] {mac}")


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
