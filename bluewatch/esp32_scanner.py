"""Optional second BLE radio: a blesploit-flashed ESP32-S3 (esp32-firmware,
https://github.com/blesploit/esp32-firmware, MIT licensed) reached over its
USB-CDC-Ethernet link and its WebSocket observer API.

The firmware only relays raw advertisement bytes -- it does no
identification of its own -- so this module's job is (1) speak the
WebSocket protocol to get those bytes, and (2) parse the standard BLE
AD-structure envelope (length + type + data, repeated) into the same
manufacturer_data / service_uuids / service_data / local_name / appearance
shape bleak already hands the rest of BlueWatch, so `db.upsert_device()`
and `classify_device()` don't need to know the data came from a second
radio at all.

Purely observational: this only ever starts/stops the firmware's scanner
and reads what it reports. It never uses the firmware's `central` or
`peripheral` capabilities (device connection, cloning/simulation), which
are out of scope for BlueWatch.
"""

import asyncio
import logging
import time
from typing import Callable, Optional

import aiohttp

from .scanner import ScannedDevice

logger = logging.getLogger(__name__)

_RECONNECT_DELAY = 10  # seconds between reconnect attempts when the ESP32 is unreachable
_STALE_AFTER = 300  # seconds -- drop devices from the snapshot if not re-seen this long


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
            async with session.ws_connect(url, timeout=10, heartbeat=30) as ws:
                self.connected = True
                logger.info(f"ESP32 scanner connected ({url})")
                await ws.send_json({"type": "scanner", "action": "start"})
                async for msg in ws:
                    if not self._running:
                        break
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        self._handle_message(msg.data)
                    elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSED):
                        break

    def _handle_message(self, raw: str) -> None:
        import json
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return
        if data.get("type") != "scan_device":
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
