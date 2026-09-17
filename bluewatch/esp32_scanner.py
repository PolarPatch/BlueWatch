"""Optional second BLE radio: a blesploit-flashed ESP32-S3 (esp32-firmware,
https://github.com/blesploit/esp32-firmware, MIT licensed) reached over its
USB-CDC-Ethernet link and its WebSocket observer API.

Two independent things live here:

1. Passive background scanning (ESP32Scanner) -- the firmware only relays
   raw advertisement bytes for this, so this module parses the standard
   BLE AD-structure envelope (length + type + data, repeated) into the
   same manufacturer_data / service_uuids / service_data / local_name /
   appearance shape bleak already hands the rest of BlueWatch, so
   `db.upsert_device()` and `classify_device()` don't need to know the
   data came from a second radio at all.

2. On-demand "Scan Unit" GATT reads (poll_ble_device_via_esp32) -- the
   same one-shot, read-only service/characteristic enumeration
   active_scan.py already does against the onboard adapter via bleak,
   just issued through the ESP32's `scanner`/`connect` command instead.
   This is the *only* connection-forming operation used here, and it
   mirrors an existing BlueWatch feature exactly (identification only,
   one operator-triggered device at a time, no persistent link kept
   afterward) -- the firmware's `central` library-session and
   `peripheral` simulation capabilities are still never touched.
"""

import asyncio
import json
import logging
import time
from typing import Callable, Optional

import aiohttp

from .scanner import ScannedDevice

logger = logging.getLogger(__name__)

_RECONNECT_DELAY = 10  # seconds between reconnect attempts when the ESP32 is unreachable
_STALE_AFTER = 300  # seconds -- drop devices from the snapshot if not re-seen this long
_CONNECT_TIMEOUT = 25.0  # overall wait for a Scan Unit scan_discovery_result / failure


def _base_uuid_from_16bit(value: int) -> str:
    return f"0000{value:04x}-0000-1000-8000-00805f9b34fb"


def _base_uuid_from_32bit(value: int) -> str:
    return f"{value:08x}-0000-1000-8000-00805f9b34fb"


def _uuid_from_128bit_le(data: bytes) -> str:
    # BLE transmits 128-bit UUIDs little-endian; standard UUID string form is big-endian.
    b = bytes(reversed(data))
    hexstr = b.hex()
    return f"{hexstr[0:8]}-{hexstr[8:12]}-{hexstr[12:16]}-{hexstr[16:20]}-{hexstr[20:32]}"


def parse_ad_structures(hex_str: str) -> dict:
    """Parse a raw BLE advertisement/scan-response payload (hex string, no
    separators) into the AD-structure envelope: length(1) + type(1) +
    data(length-1), repeated until exhausted. Returns a dict shaped like
    the fields bleak's AdvertisementData exposes."""
    result = {
        "manufacturer_data": {},
        "service_uuids": [],
        "service_data": {},
        "local_name": None,
        "appearance": None,
    }
    if not hex_str:
        return result
    try:
        data = bytes.fromhex(hex_str)
    except ValueError:
        return result

    i = 0
    n = len(data)
    while i < n:
        length = data[i]
        if length == 0:
            break
        end = i + 1 + length
        if end > n:
            break
        ad_type = data[i + 1]
        payload = data[i + 2:end]
        i = end

        if ad_type in (0x02, 0x03):  # 16-bit Service UUID list
            for j in range(0, len(payload) - 1, 2):
                value = payload[j] | (payload[j + 1] << 8)
                result["service_uuids"].append(_base_uuid_from_16bit(value))
        elif ad_type in (0x04, 0x05):  # 32-bit Service UUID list
            for j in range(0, len(payload) - 3, 4):
                value = int.from_bytes(payload[j:j + 4], "little")
                result["service_uuids"].append(_base_uuid_from_32bit(value))
        elif ad_type in (0x06, 0x07):  # 128-bit Service UUID list
            for j in range(0, len(payload) - 15, 16):
                result["service_uuids"].append(_uuid_from_128bit_le(payload[j:j + 16]))
        elif ad_type in (0x08, 0x09):  # Shortened / Complete Local Name
            try:
                name = payload.decode("utf-8", errors="ignore").strip("\x00")
            except Exception:
                name = None
            if name:
                # Complete (0x09) name wins over a shortened (0x08) one if both appear.
                if ad_type == 0x09 or not result["local_name"]:
                    result["local_name"] = name
        elif ad_type == 0x16 and len(payload) >= 2:  # Service Data - 16-bit UUID
            uuid = _base_uuid_from_16bit(payload[0] | (payload[1] << 8))
            result["service_data"][uuid] = bytes(payload[2:])
        elif ad_type == 0x20 and len(payload) >= 4:  # Service Data - 32-bit UUID
            uuid = _base_uuid_from_32bit(int.from_bytes(payload[0:4], "little"))
            result["service_data"][uuid] = bytes(payload[4:])
        elif ad_type == 0x21 and len(payload) >= 16:  # Service Data - 128-bit UUID
            uuid = _uuid_from_128bit_le(payload[0:16])
            result["service_data"][uuid] = bytes(payload[16:])
        elif ad_type == 0x19 and len(payload) >= 2:  # Appearance
            result["appearance"] = payload[0] | (payload[1] << 8)
        elif ad_type == 0xFF and len(payload) >= 2:  # Manufacturer Specific Data
            company_id = payload[0] | (payload[1] << 8)
            result["manufacturer_data"][company_id] = bytes(payload[2:])

    return result


def _merge_ad(adv: dict, scan_rsp: dict) -> dict:
    """Combine the advertisement's and scan response's parsed AD
    structures into one record -- a real device's identity is often
    split across both (e.g. the Tesla key fob's iBeacon UUID is in
    adv_data, its name only shows up in scan_rsp)."""
    merged = {
        "manufacturer_data": {**adv["manufacturer_data"], **scan_rsp["manufacturer_data"]},
        "service_uuids": list(dict.fromkeys(adv["service_uuids"] + scan_rsp["service_uuids"])),
        "service_data": {**adv["service_data"], **scan_rsp["service_data"]},
        "local_name": scan_rsp["local_name"] or adv["local_name"],
        "appearance": adv["appearance"] if adv["appearance"] is not None else scan_rsp["appearance"],
    }
    return merged


class ESP32Scanner:
    """WebSocket client for a blesploit ESP32-S3's observer API. Runs its
    own reconnect loop in the background; `snapshot()` returns whatever
    it has accumulated so far, mirroring BluetoothScanner._snapshot_ble_devices()."""

    def __init__(self, host: str = "192.168.5.1", vendor_lookup: Optional[Callable] = None):
        self.host = host
        self._vendor_lookup = vendor_lookup
        self._live: dict[str, dict] = {}  # addr -> {"merged": dict, "rssi": int, "seen_at": float}
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self.connected = False
        self._ws = None  # the active ClientWebSocketResponse, set only while connected
        # A Scan Unit "connect and read GATT" request in flight on this
        # SAME connection -- the firmware only accepts one WebSocket
        # client at a time (confirmed live: a second connection gets
        # closed immediately), so Scan Unit has to share this persistent
        # link rather than opening its own. Only one such request can be
        # in flight at once anyway (matches active_scan.py's existing
        # one-at-a-time design), so a single pending future is enough --
        # no request-id bookkeeping needed.
        self._pending_connect: Optional[asyncio.Future] = None

    def start(self) -> None:
        if self._task is not None:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_forever())
        logger.info(f"ESP32 scanner starting (host={self.host})")

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None
        self.connected = False

    async def _run_forever(self) -> None:
        while self._running:
            try:
                await self._connect_and_scan()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning(f"ESP32 scanner connection error ({self.host}): {e}")
            self.connected = False
            if not self._running:
                return
            await asyncio.sleep(_RECONNECT_DELAY)

    async def _connect_and_scan(self) -> None:
        url = f"ws://{self.host}/ws"
        async with aiohttp.ClientSession() as session:
            # ws_connect's own `timeout` kwarg is not a reliable hard
            # deadline on an unroutable/dark address (e.g. the ESP32
            # enabled in Config but physically unplugged) -- confirmed by
            # testing against a blackholed IP, where it hung well past
            # its stated 10s. Wrapping in wait_for() guarantees this
            # reconnect attempt gives up and retries instead of stalling
            # the loop for however long the OS's own TCP SYN retries take
            # (which can be minutes).
            async with await asyncio.wait_for(
                session.ws_connect(url, heartbeat=30), timeout=10,
            ) as ws:
                self.connected = True
                self._ws = ws
                logger.info(f"ESP32 scanner connected ({url})")
                await ws.send_json({"type": "scanner", "action": "start"})
                try:
                    async for msg in ws:
                        if not self._running:
                            break
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            self._handle_message(msg.data)
                        elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSED):
                            break
                finally:
                    self._ws = None
                    if self._pending_connect is not None and not self._pending_connect.done():
                        self._pending_connect.set_result(
                            {"ok": False, "error": "ESP32 connection closed unexpectedly.", "esp32_unreachable": True}
                        )

    async def connect_and_read(self, mac: str, timeout: float = _CONNECT_TIMEOUT) -> dict:
        """Scan Unit entry point: connect to `mac` through this ESP32 and
        enumerate its GATT services/characteristics, on the SAME
        persistent connection background scanning uses (see the
        firmware single-client note above). Mirrors
        active_scan.poll_ble_device()'s bleak-based result shape
        exactly, so callers don't need to know which radio answered."""
        if not self.connected or self._ws is None:
            return {"ok": False, "error": "ESP32 scanner not connected", "esp32_unreachable": True}
        if self._pending_connect is not None and not self._pending_connect.done():
            return {"ok": False, "error": "ESP32 is already busy with another Scan Unit request"}

        loop = asyncio.get_event_loop()
        future: asyncio.Future = loop.create_future()
        self._pending_connect = future
        try:
            # Stop-before-connect: the ESP32's single BLE radio can't
            # service a GATT connect while its own scanner is running
            # (confirmed live -- a connect attempt during an active scan
            # never got a reply). Scanning resumes in the finally block
            # below; ESP32Scanner's normal message loop above just picks
            # scan_device advertisements back up automatically, no
            # reconnect needed.
            await self._ws.send_json({"type": "scanner", "action": "stop"})
            await self._ws.send_json({"type": "scanner", "action": "connect", "addr": mac, "read_values": True})
            try:
                return await asyncio.wait_for(future, timeout=timeout)
            except asyncio.TimeoutError:
                return {"ok": False, "error": "Timed out waiting for the ESP32 to finish connecting."}
        except (OSError, aiohttp.ClientError) as e:
            return {"ok": False, "error": f"Could not reach the ESP32 scanner: {e}", "esp32_unreachable": True}
        finally:
            self._pending_connect = None
            if self.connected and self._ws is not None:
                try:
                    await self._ws.send_json({"type": "scanner", "action": "start"})
                except Exception:
                    pass

    def _handle_message(self, raw: str) -> None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return

        msg_type = data.get("type")
        if self._pending_connect is not None and not self._pending_connect.done():
            if msg_type == "scan_discovery_result":
                self._pending_connect.set_result(_parse_discovery_result(data))
                return
            if msg_type == "connection_progress":
                status = (data.get("status") or "").lower()
                if any(word in status for word in ("fail", "error", "timeout", "timed out")):
                    detail = data.get("detail") or data.get("status") or "unknown reason"
                    self._pending_connect.set_result(
                        {"ok": False, "error": _friendly_connect_error(detail)}
                    )
                    return
            elif msg_type == "smp" and str(data.get("status")).lower() == "failed":
                self._pending_connect.set_result(
                    {"ok": False, "error": data.get("detail") or "Pairing/authentication failed"}
                )
                return

        if msg_type != "scan_device":
            return

        addr = data.get("addr")
        if not addr:
            return

        adv = parse_ad_structures(data.get("adv_data") or "")
        scan_rsp = parse_ad_structures(data.get("scan_rsp") or "")
        merged = _merge_ad(adv, scan_rsp)

        name = merged["local_name"]
        if not name:
            top_name = data.get("name")
            if top_name and top_name != "Unknown":
                name = top_name

        self._live[addr] = {
            "merged": merged,
            "name": name,
            "rssi": data.get("rssi"),
            "seen_at": time.monotonic(),
        }

    async def snapshot(self) -> list[ScannedDevice]:
        now = time.monotonic()
        devices: list[ScannedDevice] = []
        for addr, entry in list(self._live.items()):
            if now - entry["seen_at"] > _STALE_AFTER:
                del self._live[addr]
                continue
            merged = entry["merged"]
            vendor = None
            if self._vendor_lookup:
                try:
                    vendor = await self._vendor_lookup(addr)
                except Exception:
                    vendor = None
            devices.append(ScannedDevice(
                mac=addr,
                name=entry["name"],
                rssi=entry["rssi"] if entry["rssi"] is not None else -100,
                vendor=vendor,
                service_uuids=list(merged["service_uuids"]),
                bt_type="ble",
                manufacturer_data=dict(merged["manufacturer_data"]),
                service_data=dict(merged["service_data"]),
                appearance=merged["appearance"],
            ))
        return devices


# ---------------------------------------------------------------------------
# Shared helpers for parsing the ESP32's `scan_discovery_result` (used by
# ESP32Scanner.connect_and_read() above, over its persistent connection --
# see the firmware single-client note there for why this isn't a separate
# one-shot connection). See
# https://github.com/blesploit/esp32-firmware/blob/main/docs/API.md
# ("Client -> server (by type)" / `scanner` `connect`, and
# `scan_discovery_result`), verified against the live device.

_BLE_PROPERTY_BITS = [
    (0x01, "broadcast"),
    (0x02, "read"),
    (0x04, "write-without-response"),
    (0x08, "write"),
    (0x10, "notify"),
    (0x20, "indicate"),
    (0x40, "authenticated-signed-writes"),
    (0x80, "extended-properties"),
]


def _decode_properties(bitmask) -> list:
    if not isinstance(bitmask, int):
        return []
    return [name for bit, name in _BLE_PROPERTY_BITS if bitmask & bit]


def _expand_uuid(short: str) -> str:
    """The ESP32 reports 16-/32-bit UUIDs as bare hex ("180a", "2a29")
    rather than the full 128-bit base-UUID string form the rest of
    BlueWatch (and bleak) uses -- expand so lookups against
    DEVICE_INFO_CHARACTERISTICS and friends still match. A already-full
    (128-bit, has dashes) UUID is returned unchanged."""
    s = (short or "").strip().lower()
    if len(s) == 4:
        return f"0000{s}-0000-1000-8000-00805f9b34fb"
    if len(s) == 8 and "-" not in s:
        return f"{s}-0000-1000-8000-00805f9b34fb"
    return s


def _friendly_connect_error(detail) -> str:
    """The ESP32 reports connection failures as a raw NimBLE status code
    plus internal phase number (e.g. "error: 7 (phase=1)") -- meaningful
    for debugging, but opaque to an operator reading it in the Scan Unit
    result. Phrase it the same way active_scan.py's bleak-based path
    already does for the equivalent failure, keeping the raw detail
    alongside for anyone who wants it."""
    return f"Could not connect to the device ({detail}) -- it may be out of range, not connectable, or already connected elsewhere."


def _parse_discovery_result(data: dict) -> dict:
    """Reshape a `scan_discovery_result` message into the exact
    {ok, services, device_info} shape active_scan.poll_ble_device()
    already returns from the bleak-based path, so callers don't need to
    know which radio actually answered."""
    rc = data.get("rc")
    if rc not in (0, None) or data.get("viable") is False:
        return {"ok": False, "error": _friendly_connect_error(f"rc={rc}")}

    from .active_scan import DEVICE_INFO_CHARACTERISTICS

    services = []
    device_info = {}
    for svc in data.get("services", []):
        svc_uuid = _expand_uuid(svc.get("uuid", ""))
        chars = []
        for c in svc.get("characteristics", []):
            value_obj = c.get("value") or {}
            char_uuid = _expand_uuid(value_obj.get("uuid") or c.get("uuid", ""))
            entry = {"uuid": char_uuid, "properties": _decode_properties(c.get("properties"))}
            hex_data = value_obj.get("data")
            if hex_data:
                entry["value"] = hex_data
                readable_name = DEVICE_INFO_CHARACTERISTICS.get(char_uuid)
                if readable_name:
                    try:
                        device_info[readable_name] = bytes.fromhex(hex_data).decode("utf-8").strip("\x00")
                    except (UnicodeDecodeError, ValueError):
                        device_info[readable_name] = hex_data
            chars.append(entry)
        services.append({"uuid": svc_uuid, "description": None, "characteristics": chars})

    return {"ok": True, "services": services, "device_info": device_info}


