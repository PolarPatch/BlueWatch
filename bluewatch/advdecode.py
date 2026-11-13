"""Decoders for open advertisement formats that describe a device's live
state: smart-home sensors (BTHome, Matter, HomeKit), Amazon Sidewalk,
finder networks (Google Find Hub, Apple Find My, Samsung SmartTag),
Exposure Notification and Microsoft's Nearby Sharing beacon.

Each decoder returns a "block": a small dict the web UI shows as is.

    kind       short id ("bthome", "find_hub", ...)
    title      heading on Device Details
    rows       [[label, value], ...]
    chip       optional short text for the live row (e.g. "Door open")
    alert      True when the chip is worth drawing attention to
    separated  True/False when the tracker says whether it is away from its
               owner, None when the format does not say
    tag_id     a stable id that survives address changes (SmartTag privacy
               id while separated), else absent
    name       a name worth using when the device has none

Nothing here is checked or decrypted: identifiers that rotate, hashes and
encrypted bytes are left out on purpose. Layouts follow the published specs
(BTHome v2, Matter Core spec 5.4.2.5, HAP, DULT/Find Hub, MS-CDP) and were
cross-checked against OffGridPete/Fieldwatch (MIT), v1.1.35-v1.1.44.
"""

from __future__ import annotations

import struct
from typing import Optional

COMPANY_ID_APPLE = 0x004C
COMPANY_ID_MICROSOFT = 0x0006
COMPANY_ID_AMAZON = 0x0171


def short_uuid(key) -> Optional[int]:
    """16-bit UUID from a "0000xxxx-0000-1000-8000-00805f9b34fb", "0000xxxx"
    or "xxxx" key, else None."""
    if not isinstance(key, str):
        return None
    h = key.lower().replace("-", "")
    if len(h) == 4:
        pass
    elif len(h) in (8, 32) and h.startswith("0000") and (len(h) == 8 or h.endswith("00001000800000805f9b34fb")):
        h = h[4:8]
    else:
        return None
    try:
        return int(h, 16)
    except ValueError:
        return None


def service_bytes(service_data: Optional[dict], uuid16: int) -> Optional[bytes]:
    for key, value in (service_data or {}).items():
        if short_uuid(key) == uuid16 and isinstance(value, (bytes, bytearray)):
            return bytes(value)
    return None


def has_service_uuid(service_uuids, uuid16: int) -> bool:
    return any(short_uuid(u) == uuid16 for u in (service_uuids or []))


def _block(kind: str, title: str, rows: list, chip: Optional[str] = None, alert: bool = False,
           separated: Optional[bool] = None, **extra) -> dict:
    block = {"kind": kind, "title": title, "rows": [[str(k), str(v)] for k, v in rows]}
    if chip:
        block["chip"] = chip
        block["alert"] = alert
    if separated is not None:
        block["separated"] = separated
    block.update({k: v for k, v in extra.items() if v is not None})
    return block


# --- BTHome v2 (service data FCD2) -----------------------------------------

# id -> (name, bytes, signed, factor, unit)
_BTHOME_MEASURE = {
    0x01: ("Battery", 1, False, 1, "%"),
    0x02: ("Temperature", 2, True, 0.01, "°C"),
    0x03: ("Humidity", 2, False, 0.01, "%"),
    0x04: ("Pressure", 3, False, 0.01, "hPa"),
    0x05: ("Illuminance", 3, False, 0.01, "lx"),
    0x06: ("Mass", 2, False, 0.01, "kg"),
    0x07: ("Mass", 2, False, 0.01, "lb"),
    0x08: ("Dew point", 2, True, 0.01, "°C"),
    0x09: ("Count", 1, False, 1, ""),
    0x0A: ("Energy", 3, False, 0.001, "kWh"),
    0x0B: ("Power", 3, False, 0.01, "W"),
    0x0C: ("Voltage", 2, False, 0.001, "V"),
    0x0D: ("PM2.5", 2, False, 1, "µg/m³"),
    0x0E: ("PM10", 2, False, 1, "µg/m³"),
    0x12: ("CO2", 2, False, 1, "ppm"),
    0x13: ("TVOC", 2, False, 1, "µg/m³"),
    0x14: ("Moisture", 2, False, 0.01, "%"),
    0x2E: ("Humidity", 1, False, 1, "%"),
    0x2F: ("Moisture", 1, False, 1, "%"),
    0x3D: ("Count", 2, False, 1, ""),
    0x3E: ("Count", 4, False, 1, ""),
    0x3F: ("Rotation", 2, True, 0.1, "°"),
    0x40: ("Distance", 2, False, 1, "mm"),
    0x41: ("Distance", 2, False, 0.1, "m"),
    0x42: ("Duration", 3, False, 0.001, "s"),
    0x43: ("Current", 2, False, 0.001, "A"),
    0x44: ("Speed", 2, False, 0.01, "m/s"),
    0x45: ("Temperature", 2, True, 0.1, "°C"),
    0x46: ("UV index", 1, False, 0.1, ""),
    0x47: ("Volume", 2, False, 0.1, "L"),
    0x48: ("Volume", 2, False, 1, "mL"),
    0x49: ("Volume flow rate", 2, False, 0.001, "m³/h"),
    0x4A: ("Voltage", 2, False, 0.1, "V"),
    0x4B: ("Gas", 3, False, 0.001, "m³"),
    0x4C: ("Gas", 4, False, 0.001, "m³"),
    0x4D: ("Energy", 4, False, 0.001, "kWh"),
    0x4E: ("Volume", 4, False, 0.001, "L"),
    0x4F: ("Water", 4, False, 0.001, "L"),
    0x51: ("Acceleration", 2, False, 0.001, "m/s²"),
    0x52: ("Gyroscope", 2, False, 0.001, "°/s"),
    0x55: ("Volume storage", 4, False, 0.001, "L"),
    0x56: ("Conductivity", 2, False, 1, "µS/cm"),
    0x57: ("Temperature", 1, True, 1, "°C"),
    0x58: ("Temperature", 1, True, 0.35, "°C"),
    0x59: ("Count", 1, True, 1, ""),
    0x5A: ("Count", 2, True, 1, ""),
    0x5B: ("Count", 4, True, 1, ""),
    0x5C: ("Power", 4, True, 0.01, "W"),
    0x5D: ("Current", 2, True, 0.001, "A"),
    0x5E: ("Direction", 2, False, 0.01, "°"),
    0x5F: ("Precipitation", 2, False, 0.1, "mm"),
    0x60: ("Channel", 1, False, 1, ""),
    0x61: ("Rotational speed", 2, False, 1, "rpm"),
    0x62: ("Speed", 4, True, 0.000001, "m/s"),
    0x63: ("Acceleration", 4, True, 0.000001, "m/s²"),
}

# id -> (name, off word, on word)
_BTHOME_BINARY = {
    0x0F: ("Generic", "Off", "On"),
    0x10: ("Power", "Off", "On"),
    0x11: ("Opening", "Closed", "Open"),
    0x15: ("Battery", "Normal", "Low"),
    0x16: ("Battery charging", "Not charging", "Charging"),
    0x17: ("Carbon monoxide", "Not detected", "Detected"),
    0x18: ("Cold", "Normal", "Cold"),
    0x19: ("Connectivity", "Disconnected", "Connected"),
    0x1A: ("Door", "Closed", "Open"),
    0x1B: ("Garage door", "Closed", "Open"),
    0x1C: ("Gas", "Clear", "Detected"),
    0x1D: ("Heat", "Normal", "Hot"),
    0x1E: ("Light", "No light", "Light detected"),
    0x1F: ("Lock", "Locked", "Unlocked"),
    0x20: ("Moisture", "Dry", "Wet"),
    0x21: ("Motion", "Clear", "Detected"),
    0x22: ("Moving", "Not moving", "Moving"),
    0x23: ("Occupancy", "Clear", "Detected"),
    0x24: ("Plug", "Unplugged", "Plugged in"),
    0x25: ("Presence", "Away", "Home"),
    0x26: ("Problem", "OK", "Problem"),
    0x27: ("Running", "Not running", "Running"),
    0x28: ("Safety", "Unsafe", "Safe"),
    0x29: ("Smoke", "Clear", "Detected"),
    0x2A: ("Sound", "Clear", "Detected"),
    0x2B: ("Tamper", "Off", "On"),
    0x2C: ("Vibration", "Clear", "Detected"),
    0x2D: ("Window", "Closed", "Open"),
}
# Objects that are skipped (packet id, button/dimmer events, device info),
# with their size. Text/raw (0x53/0x54) carry a length byte.
_BTHOME_SKIP = {0x00: 1, 0x3A: 1, 0x3C: 2, 0x50: 4, 0x64: 1, 0x65: 1, 0xF0: 2, 0xF1: 4, 0xF2: 3}
_BTHOME_OPEN_IDS = (0x11, 0x1A, 0x1B, 0x2D)
_BTHOME_ALARM_IDS = (0x17, 0x1C, 0x20, 0x29)  # CO, gas, water leak, smoke
_BTHOME_MOTION_IDS = (0x21, 0x22)


def _fmt_number(value: float, factor: float) -> str:
    if factor >= 1:
        return str(int(round(value)))
    decimals = max(0, len(f"{factor:.6f}".rstrip("0").split(".")[1]))
    return f"{value:.{decimals}f}"


def decode_bthome(data: Optional[bytes]) -> Optional[dict]:
    if not data:
        return None
    info = data[0]
    encrypted = bool(info & 0x01)
    trigger = bool(info & 0x04)
    version = (info >> 5) & 0x07
    rows: list = [["Version", version]]
    if encrypted or version != 2:
        if encrypted:
            rows.append(["Payload", "encrypted (not opened)"])
        return _block("bthome", "BTHome sensor", rows)
    if trigger:
        rows.append(["Sends", "on change only"])
    states: dict[int, int] = {}
    i = 1
    while i < len(data):
        obj = data[i]
        i += 1
        if obj in _BTHOME_MEASURE:
            name, size, signed, factor, unit = _BTHOME_MEASURE[obj]
            if i + size > len(data):
                break
            raw = int.from_bytes(data[i:i + size], "little", signed=signed)
            rows.append([name, (_fmt_number(raw * factor, factor) + (" " + unit if unit else "")).strip()])
        elif obj in _BTHOME_BINARY:
            size = 1
            if i >= len(data):
                break
            name, off, on = _BTHOME_BINARY[obj]
            raw = data[i]
            states[obj] = raw
            rows.append([name, on if raw == 1 else off if raw == 0 else raw])
        elif obj in (0x53, 0x54):
            if i >= len(data):
                break
            size = 1 + data[i]
            if i + size > len(data):
                break
        elif obj in _BTHOME_SKIP:
            size = _BTHOME_SKIP[obj]
            if i + size > len(data):
                break
        else:
            break  # unknown object: sizes after it cannot be trusted
        i += size

    chip, alert = None, False
    alarm = [_BTHOME_BINARY[k][0] for k in _BTHOME_ALARM_IDS if states.get(k) == 1]
    if alarm:
        chip, alert = alarm[0] + (" detected" if alarm[0] != "Moisture" else ": wet"), True
    elif any(states.get(k) == 1 for k in _BTHOME_OPEN_IDS):
        which = next(_BTHOME_BINARY[k][0] for k in _BTHOME_OPEN_IDS if states.get(k) == 1)
        chip, alert = ("Open" if which == "Opening" else which + " open"), True
    elif any(states.get(k) == 1 for k in _BTHOME_MOTION_IDS):
        chip = "Motion"
    return _block("bthome", "BTHome sensor", rows, chip=chip, alert=alert)


# --- Matter (service data FFF6) --------------------------------------------

def decode_matter(data: Optional[bytes]) -> Optional[dict]:
    if not data:
        return None
    opcode = data[0]
    if opcode == 0x00 and len(data) >= 8:
        discriminator = data[1] | ((data[2] & 0x0F) << 8)
        vendor = struct.unpack_from("<H", data, 3)[0]
        product = struct.unpack_from("<H", data, 5)[0]
        rows = [["Mode", "commissionable (in setup)"],
                ["Vendor ID", f"0x{vendor:04X}"], ["Product ID", f"0x{product:04X}"],
                ["Discriminator", discriminator]]
        if data[7] & 0x01:
            rows.append(["Additional data", "yes"])
        if data[7] & 0x02:
            rows.append(["Extended announcement", "yes"])
        return _block("matter", "Matter", rows, chip="Matter setup")
    if opcode == 0x02 and len(data) == 21:
        return _block("matter", "Matter", [["Mode", "proximity ranging"]])
    return _block("matter", "Matter", [["Opcode", f"0x{opcode:02X}"], ["Bytes", len(data)]])


# --- Apple Continuity TLVs: HomeKit (0x06) and Find My (0x12) ---------------

HOMEKIT_CATEGORIES = {
    0: "Bridged accessory", 1: "Other", 2: "Bridge", 3: "Fan", 4: "Garage door opener",
    5: "Lighting", 6: "Lock", 7: "Outlet", 8: "Switch", 9: "Thermostat", 10: "Sensor",
    11: "Security system", 12: "Door", 13: "Window", 14: "Window covering",
    15: "Programmable switch", 16: "Range extender", 17: "IP camera", 19: "Air purifier",
    20: "Heater", 21: "Air conditioner", 22: "Humidifier", 23: "Dehumidifier",
    28: "Sprinkler", 29: "Faucet", 30: "Shower system",
}


def _apple_tlvs(payload: bytes) -> list[tuple[int, bytes]]:
    """Apple TLVs. HomeKit (0x06) often writes a length longer than the
    element (0x2D/0x31); then the rest of the payload is its value."""
    out = []
    i = 0
    while i + 2 <= len(payload):
        t, n = payload[i], payload[i + 1]
        rest = len(payload) - (i + 2)
        if t == 0x06:
            take = n if 1 <= n <= rest else rest
            if take <= 0:
                break
            out.append((t, payload[i + 2:i + 2 + take]))
            i += 2 + take
            continue
        if n <= 0 or n > rest:
            break
        out.append((t, payload[i + 2:i + 2 + n]))
        i += 2 + n
    return out


def decode_homekit(value: bytes) -> Optional[dict]:
    if len(value) < 9:
        return None
    paired = not (value[0] & 0x01)
    category = struct.unpack_from("<H", value, 7)[0]
    cat_name = HOMEKIT_CATEGORIES.get(category, f"category {category}")
    rows = [["Category", cat_name], ["Paired", "yes" if paired else "no (waiting for setup)"]]
    if len(value) >= 11:
        rows.append(["State number", struct.unpack_from("<H", value, 9)[0]])
    if len(value) >= 12:
        rows.append(["Config number", value[11]])
    return _block("homekit", "HomeKit accessory", rows,
                  chip=None if paired else f"HomeKit {cat_name.lower()} unpaired",
                  name=f"HomeKit {cat_name}")


_FINDMY_BATTERY = {0: "full", 1: "medium", 2: "low", 3: "critical"}


def decode_findmy(value: bytes) -> Optional[dict]:
    if not value:
        return None
    status = value[0]
    maintained = bool(status & 0x04)
    rows = []
    if len(value) == 25:
        rows.append(["Advertisement", "full public key (asks the Find My network to report where it is)"])
    elif len(value) == 2:
        rows.append(["Advertisement", "short form, often a tag near its owner (not certain)"])
    else:
        rows.append(["Advertisement", f"{len(value)} bytes"])
    if len(value) != 2:
        rows.append(["Owner", "seen recently" if maintained else "not seen in the current key window"])
        if maintained:
            rows.append(["Battery", _FINDMY_BATTERY[(status >> 6) & 0x03]])
    return _block("find_my", "Apple Find My", rows, near_owner_hint=len(value) == 2 or None)


# --- Google Find Hub (FEAA frames 0x40/0x41) --------------------------------

def is_find_hub(data: Optional[bytes]) -> bool:
    return bool(data) and data[0] in (0x40, 0x41) and len(data) in (21, 22, 33, 34)


def decode_find_hub(data: Optional[bytes]) -> Optional[dict]:
    if not is_find_hub(data):
        return None
    separated = data[0] == 0x41
    eid_len = 20 if len(data) in (21, 22) else 32
    rows = [["Mode", "separated from its owner (address can hold for about a day)" if separated
             else "normal mode (does not say it is with its owner)"],
            ["Ephemeral ID", f"{eid_len} bytes, rotating (not shown)"]]
    return _block("find_hub", "Google Find Hub tag", rows,
                  chip="Separated" if separated else None, alert=separated, separated=separated)


# --- Samsung SmartTag (FD5A) -------------------------------------------------

_SMARTTAG_BATTERY = {0: "very low", 1: "low", 2: "medium", 3: "full"}


def decode_smarttag(data: Optional[bytes]) -> Optional[dict]:
    if not data or len(data) < 13 or (data[0] & 0xF8) != 0x10:
        return None
    state_n = data[0] & 0x07
    separated = state_n in (1, 2, 3)
    state = {1: "separated from owner", 2: "separated from owner",
             3: "separated from owner, away more than 24 h"}.get(
        state_n, "with owner" if state_n in (4, 5, 6) else None)
    rows = []
    if state:
        rows.append(["State", state])
    rows.append(["Battery", _SMARTTAG_BATTERY[data[12] & 0x03]])
    rows.append(["UWB", "yes" if data[12] & 0x04 else "no"])
    privacy_id = data[4:12].hex().upper()
    return _block("smarttag", "Samsung SmartTag", rows,
                  chip="Separated" if separated else None, alert=separated,
                  separated=True if separated else (False if state_n in (4, 5, 6) else None),
                  tag_id=("smarttag:" + privacy_id) if separated else None)


# --- Amazon Sidewalk (company 0x0171 + service FE03) ------------------------

_SIDEWALK_MODES = {0: "normal", 1: "registration", 2: "connection request", 3: "reserved"}
_SIDEWALK_BATTERY = {0: "critical", 1: "low", 2: "normal", 3: "reserved"}
_SIDEWALK_BEACONS = {(0x04, 1): "registration", (0x03, 0): "time sync",
                     (0x06, 2): "connection request", (0x21, 0): "presence"}


def decode_sidewalk(payload: Optional[bytes]) -> Optional[dict]:
    if not payload or len(payload) < 2:
        return None
    app_id, state = payload[0], payload[1]
    mode = (state >> 1) & 0x03
    rows = [["Beacon", _SIDEWALK_BEACONS.get((app_id, mode), f"application 0x{app_id:02X}")],
            ["Mode", _SIDEWALK_MODES[mode]], ["Battery", _SIDEWALK_BATTERY[(state >> 3) & 0x03]]]
    if not state & 0x01:
        rows.append(["Protocol", "not BLE (LoRa/FSK link announced)"])
    return _block("sidewalk", "Amazon Sidewalk", rows,
                  chip="Sidewalk registration" if mode == 1 else None)


# --- Exposure Notification (FD6F) --------------------------------------------

def decode_exposure(data: Optional[bytes]) -> Optional[dict]:
    if data is None:
        return None
    if len(data) == 20:
        rows = [["Identifier", "rolling proximity identifier (rotates, not shown)"],
                ["Metadata", "encrypted (not shown)"]]
    else:
        rows = [["Payload", f"{len(data)} bytes"]]
    return _block("exposure", "Exposure Notification (contact tracing)", rows)


# --- Microsoft CDP / Nearby Sharing (company 0x0006) ------------------------

_MS_DEVICE_TYPES = {
    1: "Xbox", 6: "iPhone", 7: "iPad", 8: "Android device", 9: "Windows desktop",
    11: "Windows phone", 12: "Linux device", 13: "Windows IoT", 14: "Surface Hub",
    15: "Windows laptop", 16: "Windows tablet",
}


def decode_microsoft(payload: Optional[bytes]) -> Optional[dict]:
    if not payload or len(payload) < 2 or payload[0] != 0x01:
        return None
    kind = _MS_DEVICE_TYPES.get(payload[1] & 0x1F, f"type {payload[1] & 0x1F}")
    rows = [["Device", kind]]
    name = None
    if len(payload) >= 3:
        sharing = payload[2] & 0x1F
        if sharing in (0, 1):
            rows.append(["Nearby sharing", "everyone nearby" if sharing == 1 else "my devices only"])
        # "Everyone nearby" puts the computer name from byte 10 on.
        if sharing == 1 and 11 <= len(payload) <= 25:
            raw = payload[10:]
            if all(0x20 <= b <= 0x7E for b in raw):
                name = raw.decode("ascii").strip() or None
                if name:
                    rows.append(["Computer name", name])
    return _block("ms_cdp", "Microsoft Nearby Sharing", rows, name=name)


# --- everything ---------------------------------------------------------------

def decode_adv_state(manufacturer_data: Optional[dict], service_data: Optional[dict],
                     service_uuids: Optional[list] = None) -> Optional[list[dict]]:
    """All blocks this advertisement carries, or None."""
    blocks: list[dict] = []
    mfg = manufacturer_data or {}

    def add(block):
        if block:
            blocks.append(block)

    add(decode_bthome(service_bytes(service_data, 0xFCD2)))
    add(decode_matter(service_bytes(service_data, 0xFFF6)))
    apple = mfg.get(COMPANY_ID_APPLE)
    if apple:
        for t, value in _apple_tlvs(bytes(apple)):
            if t == 0x06:
                add(decode_homekit(value))
            elif t == 0x12:
                add(decode_findmy(value))
    feaa = service_bytes(service_data, 0xFEAA)
    if is_find_hub(feaa):
        add(decode_find_hub(feaa))
    add(decode_smarttag(service_bytes(service_data, 0xFD5A)))
    if COMPANY_ID_AMAZON in mfg and (has_service_uuid(service_uuids, 0xFE03)
                                     or service_bytes(service_data, 0xFE03) is not None):
        add(decode_sidewalk(bytes(mfg[COMPANY_ID_AMAZON])))
    add(decode_exposure(service_bytes(service_data, 0xFD6F)))
    if COMPANY_ID_MICROSOFT in mfg:
        add(decode_microsoft(bytes(mfg[COMPANY_ID_MICROSOFT])))
    return blocks or None


def separated_state(blocks: Optional[list[dict]]) -> Optional[bool]:
    """True if any block says the tracker is away from its owner, False if
    one says it is with its owner, None if nothing says."""
    values = [b["separated"] for b in (blocks or []) if "separated" in b]
    if True in values:
        return True
    if False in values:
        return False
    return None


def name_hint(blocks: Optional[list[dict]]) -> Optional[str]:
    for b in blocks or []:
        if b.get("name"):
            return b["name"]
    return None


def tag_id(blocks: Optional[list[dict]]) -> Optional[str]:
    for b in blocks or []:
        if b.get("tag_id"):
            return b["tag_id"]
    return None
