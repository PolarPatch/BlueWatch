"""Remote ears: extra passive BLE listeners that report what they hear.

An "ear" is anything that already listens to Bluetooth somewhere else in the
house -- Home Assistant with its Bluetooth proxies (bluewatch-ears-ha), a
second Raspberry Pi running `bluewatch-ear`, or a test script -- and posts
short batches of advertisements to this BlueWatch. One ear can carry several
"listeners" (e.g. every ESPHome proxy behind one Home Assistant), and each
heard advert says which listener heard it, so Device Details can show which
room a device is nearest to.

Listen-only end to end: ears forward what they passively hear, BlueWatch never
sends anything back to them except the HTTP reply.

The wire format (v1) is deliberately small:

    POST /api/ears/v1/heard          Authorization: Bearer <ear token>
    {"v": 1, "sent": <ear unix time>, "software": "...",
     "heard": [{"mac": "AA:BB:..", "rssi": -61, "at": <ear unix time>,
                "by": "Kitchen", "name": "..", "tx": -59,
                "m": {"76": "<hex>"}, "u": ["180f", "<uuid>"],
                "s": {"fe2c": "<hex>"}}]}

`at` and `sent` are both read from the ear's own clock, so the age of an
observation is `sent - at` and a skewed ear clock does not matter.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import time
from dataclasses import dataclass, field
from typing import Optional

from .scanner import ScannedDevice

PROTOCOL_VERSION = 1
TOKEN_PREFIX = "bwear_"

MAX_BODY_BYTES = 512 * 1024
MAX_HEARD_PER_BATCH = 400
MAX_AGE_SECONDS = 60.0          # older observations are skipped, not stored
MAX_FUTURE_SECONDS = 5.0
MAX_NAME_LEN = 64
MAX_LISTENER_LEN = 48
MAX_MAP_ENTRIES = 8
MAX_UUIDS = 24
MAX_PAYLOAD_BYTES = 255         # one manufacturer/service-data blob
ONLINE_SECONDS = 90             # an ear with no batch for this long is "quiet"

_MAC_RE = re.compile(r"^[0-9A-F]{2}(:[0-9A-F]{2}){5}$")
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_SHORT_UUID_RE = re.compile(r"^(?:0x)?([0-9a-f]{4}|[0-9a-f]{8})$")
_HEX_RE = re.compile(r"^(?:[0-9a-f]{2})*$")


def new_token() -> str:
    return TOKEN_PREFIX + secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def bearer_token(header: Optional[str]) -> Optional[str]:
    if not header or not header.startswith("Bearer "):
        return None
    token = header[7:].strip()
    return token if token.startswith(TOKEN_PREFIX) and len(token) <= 128 else None


def _clean_text(value, limit: int) -> Optional[str]:
    if not isinstance(value, str):
        return None
    text = "".join(ch for ch in value if ch.isprintable()).strip()
    return text[:limit] or None


def _uuid(value) -> Optional[str]:
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    if _UUID_RE.match(v):
        return v
    m = _SHORT_UUID_RE.match(v)
    if m:
        return f"{m.group(1):0>8}-0000-1000-8000-00805f9b34fb"
    return None


def _blob(value) -> Optional[bytes]:
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    if len(v) > MAX_PAYLOAD_BYTES * 2 or not _HEX_RE.match(v):
        return None
    return bytes.fromhex(v)


@dataclass
class Heard:
    """One validated observation."""
    mac: str
    rssi: int
    age: float
    listener: str
    name: Optional[str] = None
    manufacturer_data: dict = field(default_factory=dict)
    service_uuids: list = field(default_factory=list)
    service_data: dict = field(default_factory=dict)


def parse_heard(item, sent: float) -> Optional[Heard]:
    """Validate one entry of a batch. Returns None if anything is off; a bad
    entry never rejects the rest of the batch."""
    if not isinstance(item, dict):
        return None
    mac = item.get("mac")
    if not isinstance(mac, str):
        return None
    mac = mac.strip().upper().replace("-", ":")
    if not _MAC_RE.match(mac):
        return None
    rssi = item.get("rssi")
    if isinstance(rssi, bool) or not isinstance(rssi, (int, float)) or not -127 <= rssi <= 20:
        return None
    at = item.get("at")
    if isinstance(at, bool) or not isinstance(at, (int, float)):
        return None
    age = sent - float(at)
    if age > MAX_AGE_SECONDS or age < -MAX_FUTURE_SECONDS:
        return None
    listener = _clean_text(item.get("by"), MAX_LISTENER_LEN) or "ear"

    heard = Heard(mac=mac, rssi=int(rssi), age=max(0.0, age), listener=listener,
                  name=_clean_text(item.get("name"), MAX_NAME_LEN))

    m = item.get("m")
    if isinstance(m, dict):
        for key, value in list(m.items())[:MAX_MAP_ENTRIES]:
            try:
                company = int(key)
            except (TypeError, ValueError):
                continue
            blob = _blob(value)
            if 0 <= company <= 0xFFFF and blob is not None:
                heard.manufacturer_data[company] = blob
    u = item.get("u")
    if isinstance(u, list):
        for value in u[:MAX_UUIDS]:
            uuid = _uuid(value)
            if uuid and uuid not in heard.service_uuids:
                heard.service_uuids.append(uuid)
    s = item.get("s")
    if isinstance(s, dict):
        for key, value in list(s.items())[:MAX_MAP_ENTRIES]:
            uuid, blob = _uuid(key), _blob(value)
            if uuid and blob is not None:
                heard.service_data[uuid] = blob
    return heard


def parse_batch(body) -> tuple[list[Heard], int, Optional[str]]:
    """Validate a whole batch. Returns (heard, skipped, error); a non-None
    error means the batch as a whole is unusable (HTTP 400)."""
    if not isinstance(body, dict):
        return [], 0, "body must be a JSON object"
    if body.get("v") != PROTOCOL_VERSION:
        return [], 0, f"unsupported protocol version (this BlueWatch speaks v{PROTOCOL_VERSION})"
    sent = body.get("sent")
    if isinstance(sent, bool) or not isinstance(sent, (int, float)):
        return [], 0, "'sent' must be a unix timestamp"
    items = body.get("heard")
    if not isinstance(items, list):
        return [], 0, "'heard' must be a list"
    if len(items) > MAX_HEARD_PER_BATCH:
        return [], 0, f"at most {MAX_HEARD_PER_BATCH} observations per batch"
    heard: list[Heard] = []
    for item in items:
        h = parse_heard(item, float(sent))
        if h is not None:
            heard.append(h)
    return heard, len(items) - len(heard), None


@dataclass
class _Pending:
    """What has been heard of one address since the last flush, merged over
    every ear and listener that heard it."""
    name: Optional[str] = None
    rssi: int = -127
    manufacturer_data: dict = field(default_factory=dict)
    service_uuids: list = field(default_factory=list)
    service_data: dict = field(default_factory=dict)


class EarHub:
    """In-memory meeting point between the HTTP handler (which feeds it) and
    the daemon's ingest loop (which drains it into the database)."""

    def __init__(self) -> None:
        self._pending: dict[str, _Pending] = {}
        # (mac, ear_id, listener) -> [last monotonic, last rssi, best rssi, hits]
        self._heard: dict[tuple[str, int, str], list] = {}
        # mac -> {(ear_id, listener): (monotonic time, rssi)} for "nearest ear"
        self._live: dict[str, dict[tuple[int, str], tuple[float, int]]] = {}
        # ear_id -> {"last": monotonic, "listeners": {name: monotonic}, "heard": n}
        self._ear_stats: dict[int, dict] = {}

    def take(self, ear_id: int, heard: list[Heard]) -> None:
        now = time.monotonic()
        stats = self._ear_stats.setdefault(ear_id, {"last": now, "listeners": {}, "heard": 0})
        stats["last"] = now
        stats["heard"] += len(heard)
        for h in heard:
            seen_at = now - h.age
            stats["listeners"][h.listener] = now
            p = self._pending.setdefault(h.mac, _Pending())
            if h.name:
                p.name = h.name
            p.rssi = max(p.rssi, h.rssi)
            p.manufacturer_data.update(h.manufacturer_data)
            p.service_data.update(h.service_data)
            for uuid in h.service_uuids:
                if uuid not in p.service_uuids:
                    p.service_uuids.append(uuid)
            key = (h.mac, ear_id, h.listener)
            row = self._heard.get(key)
            if row is None:
                self._heard[key] = [seen_at, h.rssi, h.rssi, 1]
            else:
                row[0] = max(row[0], seen_at)
                row[1] = h.rssi
                row[2] = max(row[2], h.rssi)
                row[3] += 1
            self._live.setdefault(h.mac, {})[(ear_id, h.listener)] = (seen_at, h.rssi)

    def drain(self) -> tuple[list[ScannedDevice], list[tuple]]:
        """Hand over everything heard since the last call: one ScannedDevice
        per address (strongest RSSI of all ears, union of what they decoded)
        and one (mac, ear_id, listener, age_seconds, last_rssi, best_rssi,
        hits) row per listener for the ear_heard table."""
        now = time.monotonic()
        pending, self._pending = self._pending, {}
        heard, self._heard = self._heard, {}
        devices = [
            ScannedDevice(
                mac=mac, name=p.name, rssi=p.rssi, service_uuids=p.service_uuids,
                manufacturer_data=p.manufacturer_data, service_data=p.service_data,
            )
            for mac, p in pending.items()
        ]
        rows = [
            (mac, ear_id, listener, max(0.0, now - v[0]), v[1], v[2], v[3])
            for (mac, ear_id, listener), v in heard.items()
        ]
        self._forget_old(now)
        return devices, rows

    def _forget_old(self, now: float) -> None:
        for mac in list(self._live):
            fresh = {k: v for k, v in self._live[mac].items() if now - v[0] <= 600}
            if fresh:
                self._live[mac] = fresh
            else:
                del self._live[mac]

    def live_for(self, mac: str) -> list[dict]:
        """Who heard this address recently, strongest first."""
        now = time.monotonic()
        out = [
            {"ear_id": ear_id, "listener": listener, "rssi": rssi,
             "seconds_ago": round(max(0.0, now - at), 1)}
            for (ear_id, listener), (at, rssi) in self._live.get(mac.upper(), {}).items()
            if now - at <= 600
        ]
        out.sort(key=lambda r: (r["seconds_ago"] > 60, -r["rssi"]))
        return out

    def ear_status(self, ear_id: int) -> dict:
        now = time.monotonic()
        stats = self._ear_stats.get(ear_id)
        if not stats:
            return {"online": False, "seconds_since": None, "listeners": [], "heard_since_start": 0}
        listeners = sorted(
            ({"name": n, "seconds_since": round(now - t)} for n, t in stats["listeners"].items()
             if now - t <= 3600),
            key=lambda r: r["name"].lower(),
        )
        since = now - stats["last"]
        return {"online": since <= ONLINE_SECONDS, "seconds_since": round(since),
                "listeners": listeners, "heard_since_start": stats["heard"]}

    def forget_ear(self, ear_id: int) -> None:
        self._ear_stats.pop(ear_id, None)
        for mac in list(self._live):
            self._live[mac] = {k: v for k, v in self._live[mac].items() if k[0] != ear_id}
            if not self._live[mac]:
                del self._live[mac]


HUB = EarHub()
