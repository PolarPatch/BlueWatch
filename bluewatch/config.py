"""Configuration for bluewatch."""

import os
from pathlib import Path

# Data directory
DATA_DIR = Path(os.environ.get("BLUEWATCH_DATA_DIR", Path.home() / ".local" / "share" / "bluewatch"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database path (can be overridden directly)
DB_PATH = Path(os.environ.get("BLUEWATCH_DB_PATH", DATA_DIR / "bluewatch.db"))

# Socket path for daemon communication
SOCKET_PATH = Path("/tmp/bluewatch.sock")

# Scanning interval in seconds
SCAN_INTERVAL = 10

# How long to scan for each cycle (seconds)
SCAN_DURATION = 5

# Bluetooth adapter (None = auto-select, or specify like "hci0")
BLUETOOTH_ADAPTER = os.environ.get("BLUEWATCH_ADAPTER", None)

# Prometheus metrics port (None = disabled)
METRICS_PORT = int(os.environ.get("BLUEWATCH_METRICS_PORT", 0)) or None

# Separate adapter for classic Bluetooth inquiry scans (None = use same as BLE).
# Setting this to a different adapter (e.g. a USB dongle) allows BLE and classic
# scans to run concurrently without adapter contention.
CLASSIC_BLUETOOTH_ADAPTER = os.environ.get("BLUEWATCH_CLASSIC_ADAPTER", None)

# Heartbeat check-in URL (None = disabled). POST JSON payload periodically.
HEARTBEAT_URL = os.environ.get("BLUEWATCH_HEARTBEAT_URL")
HEARTBEAT_INTERVAL = int(os.environ.get("BLUEWATCH_HEARTBEAT_INTERVAL", "300"))  # seconds

# Auto-prune sightings older than N days (0 = disabled)
PRUNE_DAYS = int(os.environ.get("BLUEWATCH_PRUNE_DAYS", "0"))

# When pruning, only remove stale devices with fewer than this many total
# sightings (0 = disabled; prune by age only, keeping device records).
PRUNE_MIN_SIGHTINGS = int(os.environ.get("BLUEWATCH_PRUNE_MIN_SIGHTINGS", "0"))

# Local Fast Pair Anti-Spoofing Public Key store, used by the "Scan Unit"
# Fast Pair verification feature (see fastpair.py) -- a JSON file the
# operator maintains by hand (hex Model ID -> hex/base64 64-byte public
# key), since there is no simple self-service public API for this lookup.
# Defaults under DATA_DIR so it survives reinstalls the same way the DB does.
FASTPAIR_KEYS_PATH = Path(os.environ.get("BLUEWATCH_FASTPAIR_KEYS_PATH", DATA_DIR / "fastpair_keys.json"))
