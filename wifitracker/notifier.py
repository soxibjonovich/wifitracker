from rich.console import Console

console = Console()


def notify_unknown(device) -> None:
    console.print(
        f"[bold red]⚠ UNKNOWN DEVICE[/bold red] "
        f"{device.hostname:<20} {device.mac}  {device.ip}  ({device.connection})"
    )
