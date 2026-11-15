from rich.console import Console

console = Console()


def notify_unknown(device) -> None:
    console.print(
        f"[bold red]⚠ UNKNOWN DEVICE[/bold red] "
        f"{device.hostname:<20} {device.mac}  {device.ip}  ({device.connection})"
    )


def notify_limit_blocked(mac: str, hours: float) -> None:
    console.print(f"[bold yellow]⏱ LIMIT REACHED[/bold yellow] {mac} used its {hours:g}h, blocked")


def notify_limit_unblocked(mac: str) -> None:
    console.print(f"[green]⏱ LIMIT RESET[/green] {mac} unblocked")


def notify_error(message: str) -> None:
    console.print(f"[red]✖ {message}[/red]")
