# WifiTracker

A CLI tool for managing your TP-Link Wifi routers — monitor connected devices, trust/block them, and run a background daemon on Raspberry Pi.

---

## Preview

![Connected Devices](assets/sample_1.png)

---

## Features

- 📋 List all connected devices with status (trusted / unknown / blocked)
- ✅ Trust devices, block / unblock them on the router (Archer C24 / C80)
- ⏳ Daily online-time limit per device — blocked after N hours, unblocked next day
- ⏱ See how long each device has been online
- 🔍 Filter only active devices
- 🤖 Background monitor daemon — alerts on unknown devices
- 🚫 Auto-block unknown devices
- 📶 Enable/disable WiFi bands (2.4GHz / 5GHz)
- 🔁 Reboot the router from the terminal

---

## Setup

### 1. Install dependencies

```bash
uv sync
```

Blocking needs `block_device` from the [TP-Link-Archer-C6U fork](https://github.com/soxibjonovich/TP-Link-Archer-C6U); `pyproject.toml` installs it from there.

### 2. Configure router credentials

```bash
python -m wifitracker setup --host http://192.168.1.1 --password yourpassword
```

Credentials are saved to `~/.wifitracker/setup.json` and loaded automatically.

---

## Usage

Notice that you can use commands with prefix `python -m` as well as without it `wifitracker devices list`

### Devices

```bash
# List all connected devices
python -m wifitracker devices list

# Show only active devices
python -m wifitracker devices list --only-active

# Trust a device
python -m wifitracker devices trust AA:BB:CC:DD:EE:FF

# Untrust a device
python -m wifitracker devices untrust AA:BB:CC:DD:EE:FF

# Block a device
python -m wifitracker devices block AA:BB:CC:DD:EE:FF

# Unblock a device
python -m wifitracker devices unblock AA:BB:CC:DD:EE:FF

# Show what the router has blocked
python -m wifitracker devices blocked
```

Block / unblock change the router's Access Control blacklist (Archer C24 / C80). Other routers print a "cannot block devices" error.

### Daily limits

```bash
# Allow a device 2.5 hours online per day
python -m wifitracker devices limit AA:BB:CC:DD:EE:FF 2.5 --name "Kid tablet"

# Show limits and today's online time
python -m wifitracker devices limits

# Remove the limit (the monitor unblocks it on its next scan)
python -m wifitracker devices unlimit AA:BB:CC:DD:EE:FF
```

Online time is counted by the monitor, so `monitor start` has to be running. Every scan adds the time since the previous scan to each active device with a limit. When a device uses up its hours it is blocked on the router; at midnight the count resets and it is unblocked. A device you blocked by hand stays blocked.

### Monitor

```bash
# Start background monitor
python -m wifitracker monitor start

# Start and auto-block unknown devices
python -m wifitracker monitor start --auto-block

# Check monitor status
python -m wifitracker monitor status

# Stop monitor
python -m wifitracker monitor stop
```

### WiFi

```bash
# Turn off 5GHz band
python -m wifitracker wifi off 5g

# Turn on 5GHz band
python -m wifitracker wifi on 5g
```

### Reboot

```bash
python -m wifitracker reboot
```

---

## Project Structure

```
wifitracker/
├── wifitracker/
│   ├── config.py        ← settings and setup file loader
│   ├── router.py        ← tplinkrouterc6u wrapper
│   ├── trust_store.py   ← JSON persistence for trusted/blocked devices
│   ├── limits.py        ← daily online-time limits and usage
│   ├── monitor.py       ← background daemon
│   ├── notifier.py      ← terminal alerts
│   └── main.py          ← Typer CLI entry point
└── tests/
    ├── test_cli.py
    ├── test_limits.py
    ├── test_router.py
    ├── test_trust_store.py
    └── test_monitor.py
```

---

## Running Tests

```bash
uv run pytest
```

---

## Raspberry Pi — Run on Boot

```ini
# /etc/systemd/system/wifitracker.service
[Unit]
Description=WifiTracker Monitor
After=network.target

[Service]
ExecStart=/usr/bin/python -m wifitracker monitor start --auto-block
WorkingDirectory=/home/pi/wifitracker
Restart=on-failure
User=pi

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable wifitracker
sudo systemctl start wifitracker
```
