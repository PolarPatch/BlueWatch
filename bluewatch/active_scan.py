"""On-demand active device polling ("Scan Unit").

Unlike the rest of BlueWatch, which only ever listens to advertisements a
device broadcasts on its own, this module actively contacts one specific
device the operator has chosen (BLE: GATT service/characteristic
discovery via a real connection; Classic: SDP service-record browsing via
sdptool) to ask it directly what it supports. This is meaningfully more
intrusive than passive scanning, so it is never run automatically -- only
triggered one device at a time from the UI.
"""

import asyncio
import logging
import re
from typing import Optional

from bleak import BleakClient

logger = logging.getLogger(__name__)

BLE_TIMEOUT = 12.0
CLASSIC_TIMEOUT = 15.0

# Set for the duration of an active Scan Unit poll (both BLE and Classic)
# so the passive scan loop (daemon.py) can skip starting a new discovery
# cycle rather than competing with it for the adapter -- an operator
# explicitly asking about one device takes priority over the background
# sweep, which just picks back up on its own once this clears.
SCAN_IN_PROGRESS = asyncio.Event()

# The daemon registers its live ESP32Scanner instance here (see
# daemon.py's _esp32_scanner_manager) whenever the optional ESP32-S3
# second radio is enabled and connected, and clears it back to None when
# disabled/disconnected -- this module has no other way to reach that
# instance. When set, Scan Unit routes BLE polls through it instead of
# the onboard adapter, which needs no SCAN_IN_PROGRESS pause at all
# since the ESP32 is a fully independent USB radio.
_esp32_scanner_ref = None


def set_esp32_scanner(scanner) -> None:
    global _esp32_scanner_ref
    _esp32_scanner_ref = scanner

# Device Information Service (0x180A) and its standard readable
# characteristics -- the BLE analogue of an SDP service record, often
# exposing manufacturer/model/serial/firmware in plain text.
DEVICE_INFO_SERVICE_UUID = "0000180a-0000-1000-8000-00805f9b34fb"
DEVICE_INFO_CHARACTERISTICS = {
    "00002a29-0000-1000-8000-00805f9b34fb": "Manufacturer Name",
    "00002a24-0000-1000-8000-00805f9b34fb": "Model Number",
    "00002a25-0000-1000-8000-00805f9b34fb": "Serial Number",
    "00002a27-0000-1000-8000-00805f9b34fb": "Hardware Revision",
    "00002a26-0000-1000-8000-00805f9b34fb": "Firmware Revision",
    "00002a28-0000-1000-8000-00805f9b34fb": "Software Revision",
    # Insta360 GO 3S vendor-specific service (87290102-...) exposes its
    # brand/model as plain null-padded ASCII in these two characteristics
    # instead of the standard Device Information Service -- found by
    # decoding a live Scan Unit read ("Insta360" / "Insta360 GO 3S").
    # Reusing this same readable-name mechanism lets the existing
    # vendor/identifier auto-fill pick it up with no extra plumbing.
    "6aa50002-6352-4d57-a7b4-003a416fbb0b": "Manufacturer Name",
    "6aa50003-6352-4d57-a7b4-003a416fbb0b": "Model Number",
}


# On a single-adapter host, this connect attempt competes with the
# passive scan loop's own discovery cycles for the same radio -- BlueZ
# rejects a connect with "InProgress" if it lands mid-cycle. That window
# is brief (a few seconds), so a short retry loop usually finds a gap
# rather than surfacing a transient, timing-dependent error to the operator.
_INPROGRESS_RETRIES = 4
_INPROGRESS_RETRY_DELAY = 3.0


async def poll_ble_device(mac: str, adapter: Optional[str] = None) -> dict:
    """Connect to a BLE device and enumerate its GATT services/characteristics.

    Returns a dict with `ok`, `services` (list of {uuid, description,
    characteristics}), and `device_info` (readable Device Information
    Service values, if the device exposes one) -- or `ok: False` and an
    `error` message on failure/timeout.

    If an ESP32-S3 second radio is enabled and connected, the connection
    is made through it instead of the onboard adapter -- it's a fully
    independent USB radio, so it never needs the SCAN_IN_PROGRESS pause
    below at all (the passive continuous scan loop keeps running on the
    onboard adapter the whole time). Falls straight through to the
    onboard-adapter path (same priority-pause behavior as always) if no
    ESP32 is registered right now -- an operator without the extra
    hardware (or a temporarily disconnected one) sees no difference from
    before.
    """
    if _esp32_scanner_ref is not None and _esp32_scanner_ref.connected:
        result = await _esp32_scanner_ref.connect_and_read(mac)
        if not result.get("esp32_unreachable"):
            # The ESP32 answered -- whether a successful read or a genuine
            # "this device wouldn't connect" failure, that's the final
            # answer; don't also spend an onboard-adapter attempt on it.
            return result
        logger.info(f"ESP32 scanner unreachable for Scan Unit ({result.get('error')}), falling back to onboard adapter")

    kwargs = {"timeout": BLE_TIMEOUT}
    if adapter:
        kwargs["adapter"] = adapter

    SCAN_IN_PROGRESS.set()
    try:
        last_error = None
        for attempt in range(1, _INPROGRESS_RETRIES + 1):
            try:
                async with BleakClient(mac, **kwargs) as client:
                    services = []
                    device_info = {}
                    for service in client.services:
                        chars = []
                        for char in service.characteristics:
                            entry = {"uuid": char.uuid, "properties": list(char.properties)}
                            if "read" in char.properties:
                                readable_name = DEVICE_INFO_CHARACTERISTICS.get(char.uuid.lower())
                                try:
                                    value = await client.read_gatt_char(char)
                                    if readable_name:
                                        try:
                                            device_info[readable_name] = value.decode("utf-8").strip("\x00")
                                        except UnicodeDecodeError:
                                            device_info[readable_name] = value.hex()
                                    entry["value"] = value.hex()
                                except Exception:
                                    pass  # Some characteristics are readable in principle but reject us -- skip silently.
                            chars.append(entry)
                        services.append({
                            "uuid": service.uuid,
                            "description": service.description,
                            "characteristics": chars,
                        })
                    return {"ok": True, "services": services, "device_info": device_info}
            except asyncio.TimeoutError:
                return {"ok": False, "error": "Timed out connecting -- device may be out of range or not connectable."}
            except Exception as e:
                last_error = e
                if "InProgress" in str(e) and attempt < _INPROGRESS_RETRIES:
                    logger.info(f"Scan Unit: adapter busy (attempt {attempt}/{_INPROGRESS_RETRIES}), retrying in {_INPROGRESS_RETRY_DELAY}s")
                    await asyncio.sleep(_INPROGRESS_RETRY_DELAY)
                    continue
                return {"ok": False, "error": str(e)}

        return {"ok": False, "error": str(last_error) if last_error else "unknown error"}
    finally:
        SCAN_IN_PROGRESS.clear()


_SDP_FIELD_RE = re.compile(r'^(Service Name|Service Description|Service Provider):\s*(.+)$', re.MULTILINE)


async def poll_classic_device(mac: str) -> dict:
    """Browse SDP service records on a Classic (BR/EDR) device via sdptool.

    Returns `ok: True` with a list of parsed service records (name/
    description/provider, where advertised), plus the raw sdptool output,
    or `ok: False` with an error message.
    """
    SCAN_IN_PROGRESS.set()
    try:
        proc = await asyncio.create_subprocess_exec(
            "sdptool", "browse", mac,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=CLASSIC_TIMEOUT)
        output = stdout.decode(errors="replace")

        if proc.returncode != 0 or "Failed to connect" in output:
            error = stderr.decode(errors="replace").strip() or "Could not connect to the device's SDP server."
            return {"ok": False, "error": error}

        # sdptool's plain output separates records with a blank line and a
        # "Service Name:"/"Service RecHandle:" header -- group by blank
        # lines rather than fully parsing the format.
        records = []
        for block in output.split("\n\n"):
            fields = dict(_SDP_FIELD_RE.findall(block))
            if fields:
                records.append(fields)

        return {"ok": True, "records": records, "raw": output}
    except asyncio.TimeoutError:
        return {"ok": False, "error": "Timed out connecting -- device may be out of range or not accepting connections."}
    except FileNotFoundError:
        return {"ok": False, "error": "sdptool is not installed on this host."}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        SCAN_IN_PROGRESS.clear()
