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
    """
    kwargs = {"timeout": BLE_TIMEOUT}
    if adapter:
        kwargs["adapter"] = adapter

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


_SDP_FIELD_RE = re.compile(r'^(Service Name|Service Description|Service Provider):\s*(.+)$', re.MULTILINE)


async def poll_classic_device(mac: str) -> dict:
    """Browse SDP service records on a Classic (BR/EDR) device via sdptool.

    Returns `ok: True` with a list of parsed service records (name/
    description/provider, where advertised), plus the raw sdptool output,
    or `ok: False` with an error message.
    """
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
