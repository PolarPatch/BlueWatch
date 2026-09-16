"""Device type classification based on vendor and patterns."""

import re
from typing import Optional

from .fastpair_models import identify_fastpair_device

# macOS CoreBluetooth provides UUIDs instead of real MAC addresses for privacy.
# These are 36-character strings like "460649E9-2306-1FF2-1272-A8D9B9D9143D".
_MACOS_UUID_RE = re.compile(
    r'^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$'
)

# Tesla's phone-key/key-fob BLE advertisement uses an iBeacon-format
# frame (via a Texas Instruments BLE chip, not an Apple one) with a
# fixed-shape local name: "S" + 16 lowercase hex chars + "C", e.g.
# "S60845be37d53334eC". Checked before the generic iBeacon classification
# below so a Tesla doesn't get labeled as a generic beacon.
_TESLA_KEY_RE = re.compile(r'^S[0-9a-f]{16}C$')

# Tesla's iBeacon frame also carries a fixed proximity UUID
# (74278bda-b644-4520-8f0c-720eaf059935) -- unlike major/minor, which
# rotate, this UUID is the constant part of the frame and identifies the
# beacon format as Tesla's specifically. A second, independent signal
# alongside the name-pattern match above (source: blesploit device
# library, https://blesplo.it/docs/device-library/).
TESLA_IBEACON_UUID = "74278bda-b644-4520-8f0c-720eaf059935"
_TESLA_IBEACON_UUID_HEX = TESLA_IBEACON_UUID.replace("-", "")

# HPE Aruba access points also identify via a fixed iBeacon proximity
# UUID, same idea as Tesla's above (source: blesploit device-library).
ARUBA_IBEACON_UUID = "4152554e-f99b-4a3b-86d0-947070693a78"
_ARUBA_IBEACON_UUID_HEX = ARUBA_IBEACON_UUID.replace("-", "")

# Aruba AP local names follow "AP-" + 12 hex chars (source: same manifest).
_ARUBA_NAME_RE = re.compile(r'^AP-[0-9a-f]{12}$', re.IGNORECASE)


def is_macos_uuid(address: str) -> bool:
    """Check if a device address is a macOS CoreBluetooth UUID.

    macOS does not expose real MAC addresses for BLE devices. Instead,
    CoreBluetooth assigns a per-device UUID that Bleak passes through.
    """
    return bool(_MACOS_UUID_RE.match(address))


def is_randomized_mac(mac: str) -> bool:
    """Check if MAC address is locally administered (randomized for privacy).

    Modern devices randomize their MAC addresses by setting the
    locally administered bit (bit 1 of first byte).

    Returns False for macOS UUID-format addresses since the bit-checking
    logic is not applicable to UUIDs.
    """
    if is_macos_uuid(mac):
        return False
    try:
        first_byte = int(mac.split(":")[0], 16)
        return bool(first_byte & 0x02)
    except (ValueError, IndexError):
        return False

# Device type constants
TYPE_PHONE = "phone"
TYPE_TABLET = "tablet"
TYPE_LAPTOP = "laptop"
TYPE_COMPUTER = "computer"
TYPE_WATCH = "watch"
TYPE_HEADPHONES = "audio"
TYPE_SPEAKER = "speaker"
TYPE_TV = "tv"
TYPE_VEHICLE = "vehicle"
TYPE_SMART_HOME = "smart"
TYPE_WEARABLE = "wearable"
TYPE_GAMING = "gaming"
TYPE_CAMERA = "camera"
TYPE_PRINTER = "printer"
TYPE_NETWORK = "network"
TYPE_TRACKER = "tracker"
TYPE_FLIPPER = "flipper"
TYPE_GLASSES = "glasses"
TYPE_BEACON = "beacon"
TYPE_MESH = "mesh"
TYPE_SKIMMER = "skimmer"
TYPE_UNKNOWN = "unknown"

# GAP Appearance (advertising AD type 0x19) is a Bluetooth SIG-standardized
# 16-bit device-category code -- the high 10 bits are a category, e.g.
# 192 = "Watch", 832 = "Heart Rate Sensor", 2112 = "Audio Sink". Unlike
# every other signal in this file it's vendor-independent, so it's a
# useful generic fallback for devices with no company-ID/UUID/name match.
# Not every peripheral includes it, and bleak only exposes it via the
# BlueZ backend's raw D-Bus properties (see scanner.py's
# _extract_appearance()). Idea from blesploit's device_type_meta manifest
# ("has_gap_device_type_hints"), category values from the Bluetooth SIG
# Assigned Numbers "Appearance Values" table. Only unambiguous categories
# are mapped -- e.g. "Remote Control"/"Control Device" are deliberately
# left out, too broad to guess a type from.
APPEARANCE_CATEGORY_MAP = {
    1: TYPE_PHONE,          # Phone
    2: TYPE_COMPUTER,       # Computer
    3: TYPE_WATCH,          # Watch
    5: TYPE_TV,             # Display
    7: TYPE_GLASSES,        # Eye-glasses
    8: TYPE_TRACKER,        # Tag
    9: TYPE_TRACKER,        # Keyring (key finders)
    12: TYPE_WEARABLE,      # Thermometer
    13: TYPE_WEARABLE,      # Heart Rate Sensor
    14: TYPE_WEARABLE,      # Blood Pressure
    15: TYPE_GAMING,        # Human Interface Device
    16: TYPE_WEARABLE,      # Glucose Meter
    17: TYPE_WEARABLE,      # Running/Walking Sensor
    18: TYPE_WEARABLE,      # Cycling
    20: TYPE_NETWORK,       # Network Device
    21: TYPE_SMART_HOME,    # Sensor
    22: TYPE_SMART_HOME,    # Light Fixtures
    23: TYPE_SMART_HOME,    # Fan
    24: TYPE_SMART_HOME,    # HVAC
    25: TYPE_SMART_HOME,    # Air Conditioning
    26: TYPE_SMART_HOME,    # Humidifier
    27: TYPE_SMART_HOME,    # Heating
    28: TYPE_SMART_HOME,    # Access Control
    30: TYPE_SMART_HOME,    # Power Device
    31: TYPE_SMART_HOME,    # Light Source
    32: TYPE_SMART_HOME,    # Window Covering
    33: TYPE_HEADPHONES,    # Audio Sink
    34: TYPE_HEADPHONES,    # Audio Source
    35: TYPE_VEHICLE,       # Motorized Vehicle
    36: TYPE_SMART_HOME,    # Domestic Appliance
    37: TYPE_HEADPHONES,    # Wearable Audio Device
    39: TYPE_TV,            # AV Equipment
    40: TYPE_TV,            # Display Equipment
    41: TYPE_WEARABLE,      # Hearing aid
    42: TYPE_GAMING,        # Gaming
}


def classify_by_appearance(appearance: Optional[int]) -> Optional[str]:
    """Classify a device from its GAP Appearance value. Returns device
    type or None if absent/unmapped."""
    if appearance is None:
        return None
    category = appearance >> 6
    return APPEARANCE_CATEGORY_MAP.get(category)


# Google Fast Pair's "Device type" category, as it appears in the bundled
# Model ID registry (see fastpair_models.py), mapped onto BlueWatch's own
# TYPE_* constants. Most rows use the named enum string; a handful of
# rarer categories only ever appear as a raw numeric ordinal in the source
# data (see fastpair_models.py's comment for how those were identified).
FASTPAIR_DEVICE_TYPE_MAP = {
    "TRUE_WIRELESS_HEADPHONES": TYPE_HEADPHONES,
    "HEADPHONES": TYPE_HEADPHONES,
    "SPEAKER": TYPE_SPEAKER,
    "WEAR_OS": TYPE_WATCH,
    "AUTOMOTIVE": TYPE_VEHICLE,
    "ANDROID_AUTO": TYPE_VEHICLE,
    "INPUT_DEVICE": TYPE_GAMING,
    "WEARABLE": TYPE_WEARABLE,
    "10": TYPE_GLASSES,   # Google Glass Enterprise Edition 2
    "11": TYPE_TRACKER,   # Tags/finders
    "12": TYPE_COMPUTER,  # Chromebook/Chromebox/Chromebase
    "13": TYPE_PHONE,     # Galaxy phones
    "16": TYPE_PRINTER,   # instax mini Link photo printers
    "17": TYPE_GAMING,    # Wireless mice (HID)
}


def identify_fastpair_type(service_data: Optional[dict]) -> Optional[str]:
    """Resolve a device type from a Fast Pair Model ID broadcast in
    service_data, via the bundled Model ID registry. Returns None if
    there's no Fast Pair service_data, the Model ID isn't in the
    registry, or its category doesn't map to a known type."""
    match = identify_fastpair_device(service_data)
    if not match or not match.get("device_type_raw"):
        return None
    return FASTPAIR_DEVICE_TYPE_MAP.get(match["device_type_raw"])

# Icons for each device type (using simple ASCII for terminal compatibility)
TYPE_ICONS = {
    TYPE_PHONE: "[PHN]",
    TYPE_TABLET: "[TAB]",
    TYPE_LAPTOP: "[LAP]",
    TYPE_COMPUTER: "[PC]",
    TYPE_WATCH: "[WCH]",
    TYPE_HEADPHONES: "[AUD]",
    TYPE_SPEAKER: "[SPK]",
    TYPE_TV: "[TV]",
    TYPE_VEHICLE: "[CAR]",
    TYPE_SMART_HOME: "[IOT]",
    TYPE_WEARABLE: "[WRB]",
    TYPE_GAMING: "[GAM]",
    TYPE_CAMERA: "[CAM]",
    TYPE_PRINTER: "[PRT]",
    TYPE_NETWORK: "[NET]",
    TYPE_TRACKER: "[TRK]",
    TYPE_FLIPPER: "[FLP]",
    TYPE_GLASSES: "[GLS]",
    TYPE_BEACON: "[BCN]",
    TYPE_MESH: "[MSH]",
    TYPE_SKIMMER: "[SKM]",
    TYPE_UNKNOWN: "[---]",
}

# Human-readable labels
TYPE_LABELS = {
    TYPE_PHONE: "Phone",
    TYPE_TABLET: "Tablet",
    TYPE_LAPTOP: "Laptop",
    TYPE_COMPUTER: "Computer",
    TYPE_WATCH: "Watch",
    TYPE_HEADPHONES: "Audio",
    TYPE_SPEAKER: "Speaker",
    TYPE_TV: "TV/Display",
    TYPE_VEHICLE: "Vehicle",
    TYPE_SMART_HOME: "Smart Home",
    TYPE_WEARABLE: "Wearable",
    TYPE_GAMING: "Gaming",
    TYPE_CAMERA: "Camera",
    TYPE_PRINTER: "Printer",
    TYPE_NETWORK: "Network",
    TYPE_TRACKER: "Tracker",
    TYPE_FLIPPER: "Flipper Zero",
    TYPE_GLASSES: "Smart Glasses (Meta)",
    TYPE_BEACON: "Beacon (iBeacon)",
    TYPE_MESH: "Mesh Radio",
    TYPE_SKIMMER: "Possible Skimmer",
    TYPE_UNKNOWN: "Unknown",
}

# Bluetooth SIG company identifiers (manufacturer-specific data), used for
# fingerprints that are far more specific than a vendor-OUI/name guess --
# see https://bitbucket.org/bluetooth-SIG/public/raw/main/assigned_numbers/company_identifiers/company_identifiers.yaml
COMPANY_ID_APPLE = 0x004C
COMPANY_ID_FLIPPER = 0x0E29
# Swapfiets e-bike lock (source: blesploit device-library)
COMPANY_ID_SWAPFIETS = 0x020F
COMPANY_ID_META_PLATFORMS = 0x01AB
COMPANY_ID_META_PLATFORMS_TECH = 0x058E
# Dedicated smart-glasses makers only -- deliberately not including
# multi-product companies (Google, Samsung, Amazon, Lenovo, etc.) since
# they'd misclassify unrelated phones/earbuds/laptops as glasses too.
COMPANY_ID_EVEN_REALITIES = 0x10F9
COMPANY_ID_VUZIX = 0x060C
COMPANY_ID_MICROSOFT = 0x0006

# More vendor company IDs (source: blesploit device-library vendor
# manifests -- each is just an icon/name match there, ported here as a
# vendor-strength signal equivalent to the existing VENDOR_PATTERNS name
# guesses, but working even when the advertised name doesn't contain the
# brand name).
COMPANY_ID_GARMIN = 0x0087
COMPANY_ID_XIAOMI = 0x038F
COMPANY_ID_SONOS = 0x05A7
COMPANY_ID_POLAR = 0x006B
COMPANY_ID_SAMSUNG = 0x0075
COMPANY_ID_SONY = 0x012D
COMPANY_ID_HUAWEI = 0x027D
COMPANY_ID_ONEPLUS = 0x072F
COMPANY_ID_LG = 0x00C4
# HPE Aruba access points (enterprise WiFi infra, not a personal device --
# useful to flag distinctly as Network rather than Unknown/generic beacon).
COMPANY_ID_ARUBA = 0x011B

# Apple's Continuity/manufacturer-data "type" byte (first byte of the
# payload after the company ID) that identifies an offline-finding /
# Find My network broadcast -- this is what an AirTag (or any other
# Find My accessory) sends while separated from its owner. Checking for
# this specific byte (rather than just company ID 0x004C, which matches
# every Apple device) is what actually distinguishes an AirTag from an
# iPhone/AirPods/etc.
APPLE_FINDMY_TYPE_BYTE = 0x12

# Apple's Continuity "Proximity Pairing" message (type 0x07 -- the same
# message type used for the AirPods pairing popup) carries a product-id
# byte at payload offset 2 (offset 4 in the raw advert, minus the 2-byte
# company ID). 0x05 there specifically means "new/unpaired AirTag" --
# the broadcast that triggers the "Connect New AirTag?" popup on a
# nearby iPhone. This catches a brand-new AirTag someone just unboxed
# nearby, before it would ever start Find My/offline-finding broadcasts
# (type 0x12 above), which only start once it's actually separated from
# an owner. Cross-checked against cifertech/ESP32-DIV's AirTag Sniffer.
APPLE_PROXIMITY_PAIRING_TYPE_BYTE = 0x07
APPLE_NEW_AIRTAG_PRODUCT_BYTE = 0x05

# When the Proximity Pairing prefix byte (payload offset 2) is 0x01 rather
# than the AirTag-setup value above, the next two bytes are a big-endian
# device-model code identifying the specific AirPods/Beats model -- cross-
# verified against two independent reverse-engineering sources that agree
# on both the byte layout and the six known model codes: furiousMAC/
# continuity (Naval Postgraduate School, GPLv2 Wireshark dissector --
# github.com/furiousMAC/continuity/blob/master/messages/proximity_pairing.md,
# value_string table in dissector/4.4.0/packet-bthci_cmd.c) and seemoo-lab/
# BTLEmap-Framework (github.com/seemoo-lab/BTLEmap-Framework,
# AirPodsBLEDecoder.swift). These are bare hex-code -> product-name facts,
# independently reimplemented here in Python, not copied source code.
APPLE_AIRPODS_PREFIX_BYTE = 0x01
APPLE_AIRPODS_MODEL_MAP: dict[int, tuple[str, str]] = {
    0x0220: ("AirPods (1st generation)", TYPE_HEADPHONES),
    0x0f20: ("AirPods (2nd generation)", TYPE_HEADPHONES),
    0x0e20: ("AirPods Pro", TYPE_HEADPHONES),
    0x0320: ("Powerbeats3", TYPE_HEADPHONES),
    0x0520: ("BeatsX", TYPE_HEADPHONES),
    0x0620: ("Beats Solo3", TYPE_HEADPHONES),
}


def identify_apple_model(manufacturer_data: Optional[dict]) -> Optional[tuple[str, str]]:
    """Identify the specific AirPods/Beats model from Apple's Continuity
    Proximity Pairing message (type 0x07), when present.

    Returns (model_name, device_type) or None if this isn't a recognized
    AirPods-family Proximity Pairing advertisement.
    """
    if not manufacturer_data:
        return None
    payload = manufacturer_data.get(COMPANY_ID_APPLE)
    if not payload or len(payload) < 5 or payload[0] != APPLE_PROXIMITY_PAIRING_TYPE_BYTE:
        return None
    if payload[2] != APPLE_AIRPODS_PREFIX_BYTE:
        return None
    model_code = (payload[3] << 8) | payload[4]
    return APPLE_AIRPODS_MODEL_MAP.get(model_code)


# Apple Continuity "Nearby Info" message (type 0x10) broadcasts a LIVE
# activity snapshot on every advertisement -- unlike everything else in
# this file (which classifies a device's fixed type), this is transient
# state that changes moment to moment, so it's never folded into
# device_type. Byte layout and the status/action nibble split verified
# against two independent sources that agree exactly: furiousMAC/
# continuity's dissector docs (github.com/furiousMAC/continuity/blob/
# master/messages/nearby_info.md) and seemoo-lab/BTLEmap-Framework's
# NearbyDecoder.swift (statusFlags = byte >> 4, actionCode = byte & 0x0F).
APPLE_NEARBY_INFO_TYPE_BYTE = 0x10

APPLE_ACTION_CODE_LABELS: dict[int, str] = {
    0x00: "unknown",
    0x01: "activity reporting disabled",
    0x03: "idle",
    0x05: "audio playing (screen locked)",
    0x07: "active (screen on)",
    0x09: "screen on, video playing",
    0x0A: "watch worn & unlocked",
    0x0B: "recent interaction",
    0x0D: "driving",
    0x0E: "phone/FaceTime call",
}
# Action codes where the screen is confirmed on vs. confirmed off -- other
# codes (unknown/disabled/driving/call/watch) don't map cleanly to a
# screen state either way, left as None rather than guessed.
_APPLE_SCREEN_ON_CODES = {0x07, 0x09}
_APPLE_SCREEN_OFF_CODES = {0x03, 0x05}


def decode_apple_activity(manufacturer_data: Optional[dict]) -> Optional[dict]:
    """Decode Apple's Continuity "Nearby Info" message (type 0x10) into a
    live activity snapshot: whether the screen is on, idle/driving/call
    state, and a couple of lower-confidence flags. Returns None if this
    isn't an Apple Nearby Info advertisement.

    Caller should recompute this on every sighting rather than caching it
    like device_type -- it reflects the device's state at the moment of
    that specific advertisement, not a fixed property of the device.
    """
    if not manufacturer_data:
        return None
    payload = manufacturer_data.get(COMPANY_ID_APPLE)
    if not payload or len(payload) < 4 or payload[0] != APPLE_NEARBY_INFO_TYPE_BYTE:
        return None

    flags_action = payload[2]
    status_flags = flags_action >> 4
    action_code = flags_action & 0x0F

    # Data Flags byte (payload[3]): furiousMAC's docs list individual bits
    # here (0x04 wifi, 0x20 watch locked, 0x80 auto-unlock enabled), but a
    # second independent decoder instead treats this whole byte as a
    # combined iOS-version/WiFi-state signature rather than clean
    # independent bits -- exposed as best-effort, lower confidence than
    # the action_code/status_flags nibbles above (which both sources
    # agree on exactly).
    data_flags = payload[3]

    return {
        "action_code": action_code,
        "activity": APPLE_ACTION_CODE_LABELS.get(action_code, f"unknown (0x{action_code:02x})"),
        "screen_on": action_code in _APPLE_SCREEN_ON_CODES if (
            action_code in _APPLE_SCREEN_ON_CODES or action_code in _APPLE_SCREEN_OFF_CODES
        ) else None,
        "primary_icloud_device": bool(status_flags & 0x01),
        "airdrop_receiving": bool(status_flags & 0x04),
        "wifi_on": bool(data_flags & 0x04),
        "watch_locked": bool(data_flags & 0x20),
        "auto_unlock_enabled": bool(data_flags & 0x80),
    }

# Samsung's manufacturer-data format for its "VD" product line (TVs,
# AV/soundbar equipment, monitors, and some appliances like fridges) --
# byte layout verified against blesploit/device-library's
# vendors/samsung/observer/adv_decode.lua (decode_vd()):
#   payload[0] = 0x42 (fixed marker), payload[1] = family (0x04 = VD)
#   payload[2] low nibble = device class, payload[3] = power state
SAMSUNG_VD_MARKER_BYTE = 0x42
SAMSUNG_VD_FAMILY_BYTE = 0x04

SAMSUNG_VD_CLASS_MAP: dict[int, tuple[str, str]] = {
    # class label -> (label, BlueWatch TYPE_*)
    0x01: ("tv", TYPE_TV),
    0x03: ("av", TYPE_SPEAKER),        # AV receiver / soundbar
    0x05: ("refrigerator", TYPE_SMART_HOME),
    0x06: ("monitor", TYPE_TV),        # "TV/Display" fits a computer monitor too
}

SAMSUNG_VD_POWER_MAP: dict[int, str] = {
    0x01: "on",
    0x40: "standby",
    0x80: "off",
}


def identify_samsung_type(manufacturer_data: Optional[dict]) -> Optional[str]:
    """Resolve a device type from Samsung's VD-family manufacturer data,
    when the device class byte is present and recognized. Static/one-time
    signal (device category doesn't change), unlike decode_samsung_status()
    below (live power state)."""
    if not manufacturer_data:
        return None
    payload = manufacturer_data.get(COMPANY_ID_SAMSUNG)
    if not payload or len(payload) < 3 or payload[0] != SAMSUNG_VD_MARKER_BYTE or payload[1] != SAMSUNG_VD_FAMILY_BYTE:
        return None
    class_info = SAMSUNG_VD_CLASS_MAP.get(payload[2] & 0x0F)
    return class_info[1] if class_info else None


def decode_samsung_status(manufacturer_data: Optional[dict]) -> Optional[dict]:
    """Decode Samsung's VD-family manufacturer data into a live power-state
    snapshot (on/standby/off). Returns None if this isn't a recognized
    Samsung VD advertisement or the state byte isn't one of the three
    known power states (e.g. it's an 0x20 "extension frame" -- metadata
    continuation, not a state to report).

    Caller should recompute this on every sighting rather than caching it
    like device_type -- power state changes over time, it's not a fixed
    property of the device."""
    if not manufacturer_data:
        return None
    payload = manufacturer_data.get(COMPANY_ID_SAMSUNG)
    if not payload or len(payload) < 4 or payload[0] != SAMSUNG_VD_MARKER_BYTE or payload[1] != SAMSUNG_VD_FAMILY_BYTE:
        return None

    class_info = SAMSUNG_VD_CLASS_MAP.get(payload[2] & 0x0F)
    power = SAMSUNG_VD_POWER_MAP.get(payload[3])
    if power is None:
        return None

    return {
        "device_class": class_info[0] if class_info else "unknown",
        "power": power,
    }


# A few more Apple Continuity message types (see nccgroup/Sniffle's
# advdata/msd_apple.py for the full reference table) that map cleanly
# to a device type without ambiguity. AirPlay Target/Source (0x09/0x0A)
# deliberately excluded -- those cover HomePod, Apple TV, and Macs
# alike, too broad to classify safely.
APPLE_AIRPRINT_TYPE_BYTE = 0x03
APPLE_HOMEKIT_TYPE_BYTE = 0x06
APPLE_IBEACON_TYPE_BYTE = 0x02
APPLE_IBEACON_MIN_LEN = 23  # type + length byte + 21-byte UUID/major/minor/power payload

# Microsoft's Swift Pair / "Nearby Share" beacon (Connected Devices
# Platform) encodes an explicit device-type byte on purpose, for the
# pairing-popup UI -- far more reliable than guessing from vendor/name.
# See https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-cdp/
# and nccgroup/Sniffle's advdata/msd_microsoft.py.
MS_SWIFT_PAIR_SCENARIO_TYPE = 1
MS_SWIFT_PAIR_DEVICE_TYPES = {
    1: TYPE_GAMING,     # Xbox One
    6: TYPE_PHONE,      # Apple iPhone
    7: TYPE_TABLET,     # Apple iPad
    8: TYPE_PHONE,      # Android device
    9: TYPE_COMPUTER,   # Windows 10 Desktop
    11: TYPE_PHONE,     # Windows 10 Phone
    12: TYPE_COMPUTER,  # Linux device
    13: TYPE_SMART_HOME,  # Windows IoT
    14: TYPE_TV,        # Surface Hub
    15: TYPE_LAPTOP,    # Windows laptop
    16: TYPE_TABLET,    # Windows tablet
}


def classify_by_manufacturer_data(manufacturer_data: Optional[dict]) -> Optional[str]:
    """
    Classify a device from its raw BLE manufacturer-specific data
    (company ID -> payload bytes). This is the most specific signal
    available, since it comes straight from the chipset/firmware rather
    than a spoofable advertised name -- checked before UUIDs/name/vendor.
    Returns device type or None if no match.
    """
    if not manufacturer_data:
        return None

    if COMPANY_ID_FLIPPER in manufacturer_data:
        return TYPE_FLIPPER

    if (COMPANY_ID_META_PLATFORMS in manufacturer_data or COMPANY_ID_META_PLATFORMS_TECH in manufacturer_data
            or COMPANY_ID_EVEN_REALITIES in manufacturer_data or COMPANY_ID_VUZIX in manufacturer_data):
        return TYPE_GLASSES

    ms_payload = manufacturer_data.get(COMPANY_ID_MICROSOFT)
    if ms_payload and len(ms_payload) >= 2 and ms_payload[0] == MS_SWIFT_PAIR_SCENARIO_TYPE:
        device_type_nibble = ms_payload[1] & 0x1F
        ms_type = MS_SWIFT_PAIR_DEVICE_TYPES.get(device_type_nibble)
        if ms_type:
            return ms_type

    apple_payload = manufacturer_data.get(COMPANY_ID_APPLE)
    if apple_payload and len(apple_payload) >= 1:
        apple_type = apple_payload[0]
        if apple_type == APPLE_FINDMY_TYPE_BYTE:
            return TYPE_TRACKER
        if (apple_type == APPLE_PROXIMITY_PAIRING_TYPE_BYTE and len(apple_payload) >= 3
                and apple_payload[2] == APPLE_NEW_AIRTAG_PRODUCT_BYTE):
            return TYPE_TRACKER
        if apple_type == APPLE_AIRPRINT_TYPE_BYTE:
            return TYPE_PRINTER
        if apple_type == APPLE_HOMEKIT_TYPE_BYTE:
            return TYPE_SMART_HOME
        if apple_type == APPLE_IBEACON_TYPE_BYTE and len(apple_payload) >= APPLE_IBEACON_MIN_LEN:
            # Tesla's phone-key/key-fob broadcasts in standard iBeacon
            # format but with a fixed proximity UUID -- check that before
            # falling back to a generic beacon classification.
            ibeacon_uuid_hex = apple_payload[2:18].hex()
            if ibeacon_uuid_hex == _TESLA_IBEACON_UUID_HEX:
                return TYPE_VEHICLE
            if ibeacon_uuid_hex == _ARUBA_IBEACON_UUID_HEX:
                return TYPE_NETWORK
            return TYPE_BEACON

    # HPE Aruba access points also identify via a distinct company ID
    # with an "08"-prefixed payload (source: blesploit device-library).
    aruba_payload = manufacturer_data.get(COMPANY_ID_ARUBA)
    if aruba_payload and aruba_payload[:1] == b"\x08":
        return TYPE_NETWORK

    return None


# Broad "this company made it, subtype unknown" company IDs -- much
# weaker than the specific fingerprints above (a single ID covers a
# vendor's whole product line, e.g. Samsung phones/TVs/SmartTags all
# share 0x0075), so this is checked as a fallback after UUID/name/
# appearance classification rather than up front with the others.
# Source: blesploit device-library vendor manifests (each just assigns
# an icon there, with no specific device-type claim of their own).
VENDOR_COMPANY_ID_MAP = {
    COMPANY_ID_GARMIN: TYPE_WATCH,
    COMPANY_ID_XIAOMI: TYPE_PHONE,
    COMPANY_ID_SONOS: TYPE_SPEAKER,
    COMPANY_ID_SAMSUNG: TYPE_PHONE,
    COMPANY_ID_SONY: TYPE_HEADPHONES,
    COMPANY_ID_ONEPLUS: TYPE_PHONE,
    COMPANY_ID_LG: TYPE_PHONE,
}


def classify_by_vendor_company_id(manufacturer_data: Optional[dict]) -> Optional[str]:
    """Weak fallback: a bare company-ID match with no specific subtype
    guarantee. Returns device type or None."""
    if not manufacturer_data:
        return None
    for company_id, device_type in VENDOR_COMPANY_ID_MAP.items():
        if company_id in manufacturer_data:
            return device_type
    return None

# Vendor patterns for classification
# Format: (pattern_to_match_in_vendor, device_type)
# Patterns are matched case-insensitively
VENDOR_PATTERNS = [
    # Phones / Mobile devices
    ("apple", TYPE_PHONE),  # Could be phone, tablet, laptop, watch - default to phone
    ("samsung electronics", TYPE_PHONE),
    ("xiaomi", TYPE_PHONE),
    ("huawei", TYPE_PHONE),
    ("oneplus", TYPE_PHONE),
    ("oppo", TYPE_PHONE),
    ("vivo", TYPE_PHONE),
    ("realme", TYPE_PHONE),
    ("motorola", TYPE_PHONE),
    ("nokia", TYPE_PHONE),
    ("lg electronics", TYPE_PHONE),
    ("zte", TYPE_PHONE),
    ("google", TYPE_PHONE),
    ("fairphone", TYPE_PHONE),
    ("nothing", TYPE_PHONE),

    # Computers / Laptops
    ("dell", TYPE_LAPTOP),
    ("lenovo", TYPE_LAPTOP),
    ("hewlett packard", TYPE_LAPTOP),
    ("hp inc", TYPE_LAPTOP),
    ("asus", TYPE_LAPTOP),
    ("acer", TYPE_LAPTOP),
    ("microsoft", TYPE_COMPUTER),
    ("intel corporate", TYPE_COMPUTER),
    ("gigabyte", TYPE_COMPUTER),
    ("msi", TYPE_COMPUTER),

    # Audio devices
    ("bose", TYPE_HEADPHONES),
    ("sony", TYPE_HEADPHONES),
    ("sennheiser", TYPE_HEADPHONES),
    ("jabra", TYPE_HEADPHONES),
    ("beats", TYPE_HEADPHONES),
    ("jbl", TYPE_SPEAKER),
    ("harman", TYPE_SPEAKER),
    ("bang & olufsen", TYPE_SPEAKER),
    ("sonos", TYPE_SPEAKER),
    ("skullcandy", TYPE_HEADPHONES),
    ("audio-technica", TYPE_HEADPHONES),
    ("plantronics", TYPE_HEADPHONES),
    ("anker", TYPE_HEADPHONES),

    # Watches / Wearables
    ("fitbit", TYPE_WATCH),
    ("garmin", TYPE_WATCH),
    ("polar", TYPE_WATCH),
    ("suunto", TYPE_WATCH),
    ("whoop", TYPE_WEARABLE),
    ("oura", TYPE_WEARABLE),

    # Smart Home / IoT
    ("amazon", TYPE_SMART_HOME),
    ("ring", TYPE_SMART_HOME),
    ("nest", TYPE_SMART_HOME),
    ("philips", TYPE_SMART_HOME),
    ("ikea", TYPE_SMART_HOME),
    ("tuya", TYPE_SMART_HOME),
    ("shelly", TYPE_SMART_HOME),
    ("switchbot", TYPE_SMART_HOME),
    ("aqara", TYPE_SMART_HOME),
    ("wyze", TYPE_SMART_HOME),
    ("eufy", TYPE_SMART_HOME),
    ("ecobee", TYPE_SMART_HOME),
    ("hue", TYPE_SMART_HOME),
    ("smartthings", TYPE_SMART_HOME),
    ("tp-link", TYPE_SMART_HOME),
    ("meross", TYPE_SMART_HOME),
    ("govee", TYPE_SMART_HOME),
    ("lifx", TYPE_SMART_HOME),
    ("nanoleaf", TYPE_SMART_HOME),
    ("yale", TYPE_SMART_HOME),
    ("august", TYPE_SMART_HOME),
    ("schlage", TYPE_SMART_HOME),

    # TVs / Displays
    ("roku", TYPE_TV),
    ("vizio", TYPE_TV),
    ("tcl", TYPE_TV),
    ("hisense", TYPE_TV),
    ("chromecast", TYPE_TV),
    ("fire tv", TYPE_TV),

    # Vehicles
    ("tesla", TYPE_VEHICLE),
    ("ford", TYPE_VEHICLE),
    ("gm", TYPE_VEHICLE),
    ("volkswagen", TYPE_VEHICLE),
    ("bmw", TYPE_VEHICLE),
    ("mercedes", TYPE_VEHICLE),
    ("audi", TYPE_VEHICLE),
    ("toyota", TYPE_VEHICLE),
    ("honda", TYPE_VEHICLE),
    ("nissan", TYPE_VEHICLE),
    ("hyundai", TYPE_VEHICLE),
    ("kia", TYPE_VEHICLE),
    ("volvo", TYPE_VEHICLE),
    ("rivian", TYPE_VEHICLE),
    ("lucid", TYPE_VEHICLE),
    ("harley", TYPE_VEHICLE),
    ("continental auto", TYPE_VEHICLE),
    ("bosch", TYPE_VEHICLE),
    ("denso", TYPE_VEHICLE),

    # Gaming
    ("nintendo", TYPE_GAMING),
    ("playstation", TYPE_GAMING),
    ("xbox", TYPE_GAMING),
    ("valve", TYPE_GAMING),
    ("razer", TYPE_GAMING),
    ("steelseries", TYPE_GAMING),
    ("logitech", TYPE_GAMING),

    # Cameras
    ("gopro", TYPE_CAMERA),
    ("canon", TYPE_CAMERA),
    ("nikon", TYPE_CAMERA),
    ("dji", TYPE_CAMERA),
    ("insta360", TYPE_CAMERA),

    # Printers
    ("epson", TYPE_PRINTER),
    ("brother", TYPE_PRINTER),
    ("xerox", TYPE_PRINTER),

    # Network equipment
    ("cisco", TYPE_NETWORK),
    ("netgear", TYPE_NETWORK),
    ("ubiquiti", TYPE_NETWORK),
    ("aruba", TYPE_NETWORK),
    ("linksys", TYPE_NETWORK),
    ("asus router", TYPE_NETWORK),
    ("eero", TYPE_NETWORK),
    ("orbi", TYPE_NETWORK),
]

# BLE Service UUID patterns for device fingerprinting
# Maps UUID patterns to device types (more specific = higher priority)
# UUIDs can be 16-bit (0x180D), 32-bit, or full 128-bit
SERVICE_UUID_PATTERNS = [
    # Wearables / Fitness
    ("0000180d", TYPE_WEARABLE),  # Heart Rate Service
    ("0000181c", TYPE_WEARABLE),  # User Data
    ("00001814", TYPE_WEARABLE),  # Running Speed and Cadence
    ("00001816", TYPE_WEARABLE),  # Cycling Speed and Cadence
    ("00001818", TYPE_WEARABLE),  # Cycling Power
    ("0000181b", TYPE_WEARABLE),  # Body Composition
    ("0000181d", TYPE_WEARABLE),  # Weight Scale

    # Health devices
    ("00001810", TYPE_WEARABLE),  # Blood Pressure
    ("00001808", TYPE_WEARABLE),  # Glucose
    ("00001809", TYPE_WEARABLE),  # Health Thermometer

    # Audio devices (A2DP and related)
    ("0000110b", TYPE_HEADPHONES),  # A2DP Audio Sink
    ("0000110a", TYPE_HEADPHONES),  # A2DP Audio Source
    ("0000111e", TYPE_HEADPHONES),  # Handsfree
    ("0000111f", TYPE_HEADPHONES),  # Handsfree Audio Gateway
    ("00001108", TYPE_HEADPHONES),  # Headset
    ("0000110d", TYPE_HEADPHONES),  # A2DP (Advanced Audio)
    ("00001203", TYPE_HEADPHONES),  # Generic Audio
    ("0000184e", TYPE_HEADPHONES),  # Audio Stream Control
    ("0000184f", TYPE_HEADPHONES),  # Broadcast Audio Scan
    ("00001850", TYPE_HEADPHONES),  # Published Audio Capabilities
    ("00001853", TYPE_HEADPHONES),  # Common Audio

    # Gaming / HID
    ("00001812", TYPE_GAMING),  # Human Interface Device (keyboards, mice, controllers)
    ("00001124", TYPE_GAMING),  # HID (legacy)

    # Apple-specific (Continuity, AirDrop, etc.)
    ("d0611e78", TYPE_PHONE),  # Apple Continuity
    ("7905f431", TYPE_PHONE),  # Apple Notification Center
    ("89d3502b", TYPE_PHONE),  # Apple Media Service
    ("0000fd6f", TYPE_PHONE),  # Apple Continuity short UUID

    # Google/Android
    ("0000fe9f", TYPE_PHONE),  # Google Fast Pair
    ("0000fe2c", TYPE_PHONE),  # Google Nearby

    # Smart Home / IoT
    ("0000181a", TYPE_SMART_HOME),  # Environmental Sensing
    ("0000fef5", TYPE_SMART_HOME),  # Philips Hue / Dialog
    ("0000fee7", TYPE_SMART_HOME),  # Tencent IoT
    ("0000feaa", TYPE_SMART_HOME),  # Google Eddystone (beacons)
    ("0000feab", TYPE_SMART_HOME),  # Nokia beacons

    # Trackers / Finders (source: jbohack/nyanBOX detector fingerprints,
    # cross-checked against Bluetooth SIG assigned 16-bit UUID numbers)
    ("0000feed", TYPE_TRACKER),  # Tile
    ("0000feec", TYPE_TRACKER),  # Tile
    ("0000fd5a", TYPE_TRACKER),  # Samsung SmartTag
    ("0000febe", TYPE_SMART_HOME),  # Bose

    # Smart glasses
    ("0000fd5f", TYPE_GLASSES),  # Meta/Ray-Ban Meta glasses

    # Off-grid mesh radio
    ("6ba1b21815a8461f9fa85dcae273eafd", TYPE_MESH),  # Meshtastic

    # Flipper Zero also advertises these 16-bit service UUIDs (in
    # addition to company ID 0x0E29, checked separately in
    # classify_by_manufacturer_data) -- source: blesploit device-library.
    ("00003081", TYPE_FLIPPER),
    ("00003082", TYPE_FLIPPER),
    ("00003083", TYPE_FLIPPER),

    # Sony Sound Connect / SongPal proprietary service UUIDs -- a more
    # specific audio-device signal than the generic Sony company ID
    # fallback below (source: blesploit device-library).
    ("5b833e05-6bc7-4802-8e9a-723ceca4bd8f".replace("-", ""), TYPE_HEADPHONES),
    ("5b833e26-6bc7-4802-8e9a-723ceca4bd8f".replace("-", ""), TYPE_HEADPHONES),
    ("5b833e28-6bc7-4802-8e9a-723ceca4bd8f".replace("-", ""), TYPE_HEADPHONES),
    ("5b833e20-6bc7-4802-8e9a-723ceca4bd8f".replace("-", ""), TYPE_HEADPHONES),

    # Note: Tesla's iOS-fallback (service UUID 0x1122) and Swapfiets
    # (service UUID 0x1580) are deliberately NOT listed here -- those
    # 16-bit UUIDs aren't specific enough alone (0x1122/0x1580 are
    # generic legacy SIG-assigned UUIDs), so they're only classified
    # when combined with a name match in classify_device().

    # Location/Navigation
    ("00001819", TYPE_WEARABLE),  # Location and Navigation

    # Watches (specific manufacturer UUIDs)
    ("cba20d00", TYPE_WATCH),  # SwitchBot
    ("0000fee0", TYPE_WATCH),  # Xiaomi Mi Band / Amazfit
    ("0000feea", TYPE_WATCH),  # Swirl Networks (wearables)

    # Printers
    ("00001118", TYPE_PRINTER),  # Direct Printing
    ("00001119", TYPE_PRINTER),  # Reference Printing

    # Camera
    ("00001822", TYPE_CAMERA),  # Camera Profile
]

# Human-readable names for common service UUIDs
SERVICE_UUID_NAMES = {
    "0000180d": "Heart Rate",
    "0000180f": "Battery",
    "00001800": "Generic Access",
    "00001801": "Generic Attribute",
    "0000180a": "Device Info",
    "00001812": "HID",
    "0000181a": "Environmental",
    "0000110b": "A2DP Sink",
    "0000110a": "A2DP Source",
    "0000fd6f": "Apple Continuity",
    "0000fe9f": "Google Fast Pair",
    "0000fee0": "Mi Band",
}


def classify_by_uuids(service_uuids: Optional[list[str]]) -> Optional[str]:
    """
    Classify a device based on its BLE service UUIDs.
    Returns device type or None if no match.
    """
    if not service_uuids:
        return None

    # Normalize UUIDs to lowercase for comparison
    normalized = [uuid.lower().replace("-", "") for uuid in service_uuids]

    # Check each UUID against patterns
    for uuid in normalized:
        for pattern, device_type in SERVICE_UUID_PATTERNS:
            if pattern in uuid:
                return device_type

    return None


def get_uuid_names(service_uuids: Optional[list[str]]) -> list[str]:
    """Get human-readable names for service UUIDs."""
    if not service_uuids:
        return []

    names = []
    for uuid in service_uuids:
        normalized = uuid.lower().replace("-", "")
        # Check for known UUIDs
        for pattern, name in SERVICE_UUID_NAMES.items():
            if pattern in normalized:
                names.append(name)
                break
    return names


# Bluetooth major device class to device type mapping
# See: https://www.bluetooth.com/specifications/assigned-numbers/baseband/
DEVICE_CLASS_MAJOR_MAP = {
    1: TYPE_COMPUTER,     # Computer
    2: TYPE_PHONE,        # Phone
    3: TYPE_NETWORK,      # LAN/Network Access Point
    4: TYPE_HEADPHONES,   # Audio/Video
    5: TYPE_GAMING,       # Peripheral (keyboard, mouse, etc.)
    6: TYPE_PRINTER,      # Imaging (printer, scanner, camera)
    7: TYPE_WEARABLE,     # Wearable
    8: TYPE_GAMING,       # Toy
    9: TYPE_WEARABLE,     # Health
}


def classify_by_device_class(device_class: Optional[int]) -> Optional[str]:
    """Classify a device based on its Classic Bluetooth device class.

    Returns device type or None if no match.
    """
    if device_class is None:
        return None

    # Major device class is bits 8-12
    major = (device_class >> 8) & 0x1F
    return DEVICE_CLASS_MAJOR_MAP.get(major)


def classify_device(
    vendor: Optional[str],
    name: Optional[str] = None,
    service_uuids: Optional[list[str]] = None,
    device_class: Optional[int] = None,
    manufacturer_data: Optional[dict] = None,
    appearance: Optional[int] = None,
    service_data: Optional[dict] = None,
) -> str:
    """
    Classify a device based on its vendor, name, service UUIDs, device
    class, GAP Appearance, Fast Pair service_data, and raw manufacturer
    data. Returns a device type constant.

    Priority: Fast Pair Model ID > Manufacturer data > Service UUIDs >
    GAP Appearance > Name patterns > Device class > Company-ID vendor
    guess > Vendor patterns
    """
    # A resolved Fast Pair Model ID names the exact product (e.g. "Sonos
    # Ace"), so it's a stronger signal than any generic UUID/company-ID
    # check below -- checked first.
    if service_data:
        fastpair_type = identify_fastpair_type(service_data)
        if fastpair_type:
            return fastpair_type

    # Samsung's VD-family manufacturer data (TVs/AV/monitors/fridges)
    # names the exact device class -- specific enough to check this early,
    # same tier as the Fast Pair Model ID check above.
    if manufacturer_data:
        samsung_type = identify_samsung_type(manufacturer_data)
        if samsung_type:
            return samsung_type

    # Tesla's key-fob/phone-key name pattern is checked first -- it would
    # otherwise get shadowed by the generic iBeacon manufacturer-data
    # classification below, since Tesla's BLE key broadcasts in iBeacon
    # format.
    if name and _TESLA_KEY_RE.match(name):
        return TYPE_VEHICLE

    # Insta360's GO 3S action camera supports Apple's third-party Find My
    # network program (it's small and easy to lose), so it genuinely
    # broadcasts a real Find My separated-from-owner signal -- which would
    # otherwise shadow it into TYPE_TRACKER below. It's fundamentally a
    # camera that happens to have Find My support, not a tracker, so this
    # is checked first (source: decoded from a live Scan Unit GATT read).
    if name and "insta360" in name.lower():
        return TYPE_CAMERA

    # iOS strips manufacturer data from adverts it surfaces to apps, so a
    # Tesla key fob seen via an iOS-based scanner may only have this
    # service UUID plus a looser name shape left to go on (source:
    # blesploit device-library).
    if name and re.match(r'^S.{17}$', name) and service_uuids:
        normalized_uuids = [u.lower().replace("-", "") for u in service_uuids]
        if any("00001122" in u for u in normalized_uuids):
            return TYPE_VEHICLE

    # Swapfiets e-bike lock: company ID + service UUID + exact name,
    # combined since none of those three is specific enough alone
    # (source: blesploit device-library).
    if (name == "Swapfiets" and service_uuids
            and manufacturer_data and COMPANY_ID_SWAPFIETS in manufacturer_data):
        normalized_uuids = [u.lower().replace("-", "") for u in service_uuids]
        if any("00001580" in u for u in normalized_uuids):
            return TYPE_VEHICLE

    # Aruba access points, combined signals not specific enough alone
    # (source: blesploit device-library).
    if name and _ARUBA_NAME_RE.match(name):
        return TYPE_NETWORK

    # Polar watches: company ID alone (0x006B) is reused elsewhere, so
    # require the name too, matching blesploit's own combined condition.
    if name and "polar" in name.lower() and manufacturer_data and COMPANY_ID_POLAR in manufacturer_data:
        return TYPE_WATCH

    # Huawei: same reasoning -- company ID + name, not either alone.
    if name and "huawei" in name.lower() and manufacturer_data and COMPANY_ID_HUAWEI in manufacturer_data:
        return TYPE_PHONE

    # Manufacturer-data fingerprints (AirTag/Find My, Flipper Zero, Meta
    # glasses) are the most specific signal available -- check first.
    if manufacturer_data:
        mfg_type = classify_by_manufacturer_data(manufacturer_data)
        if mfg_type:
            return mfg_type

    # Try UUID-based classification first (most accurate)
    if service_uuids:
        uuid_type = classify_by_uuids(service_uuids)
        if uuid_type:
            return uuid_type

    # GAP Appearance -- a standardized, vendor-independent category code.
    # Checked before name-pattern heuristics since it's a structured field
    # rather than a spoofable/inconsistent advertised string, but after
    # manufacturer-data/UUID fingerprints since those are more specific.
    appearance_type = classify_by_appearance(appearance)
    if appearance_type:
        return appearance_type

    # Check name if provided (some devices advertise their type)
    if name:
        name_lower = name.lower()

        # HC-03/05/06 are cheap classic-Bluetooth serial modules -- also
        # the modules most commonly found wired into credit-card
        # skimmers. Exact match only (source: jbohack/nyanBOX's card
        # skimmer detector), flagged distinctly rather than folded into
        # a generic type since it's worth the operator's attention.
        if name in ("HC-03", "HC-05", "HC-06"):
            return TYPE_SKIMMER

        # Off-grid mesh radio firmware (source: jbohack/nyanBOX detectors)
        if name.startswith("MeshCore-") or "meshtastic" in name_lower:
            return TYPE_MESH

        # Lime e-scooter (source: blesploit device-library)
        if re.match(r'^lime-[0-9]+$', name):
            return TYPE_VEHICLE

        # Common name patterns
        if any(x in name_lower for x in ["iphone", "android", "pixel", "galaxy s", "galaxy z"]):
            return TYPE_PHONE
        if any(x in name_lower for x in ["ipad", "tab", "tablet"]):
            return TYPE_TABLET
        if any(x in name_lower for x in ["macbook", "thinkpad", "xps", "laptop"]):
            return TYPE_LAPTOP
        if any(x in name_lower for x in ["imac", "mac mini", "mac pro", "desktop"]):
            return TYPE_COMPUTER
        if any(x in name_lower for x in ["watch", "band", "mi band"]):
            return TYPE_WATCH
        if any(x in name_lower for x in ["airpod", "buds", "earbuds", "headphone"]):
            return TYPE_HEADPHONES
        if any(x in name_lower for x in ["homepod", "echo", "speaker"]):
            return TYPE_SPEAKER
        if any(x in name_lower for x in ["tv", "roku", "firestick", "chromecast"]):
            return TYPE_TV
        if any(x in name_lower for x in ["car", "vehicle", "model 3", "model y", "model s"]):
            return TYPE_VEHICLE

    # Try Classic BT device class (more reliable than vendor guessing)
    if device_class is not None:
        class_type = classify_by_device_class(device_class)
        if class_type:
            return class_type

    # Weak company-ID-only vendor guess (see VENDOR_COMPANY_ID_MAP) --
    # more reliable than a fuzzy vendor-string match since it comes from
    # the chipset rather than an OUI/name lookup, but checked after
    # device_class since it can't distinguish a vendor's product line.
    if manufacturer_data:
        vendor_id_type = classify_by_vendor_company_id(manufacturer_data)
        if vendor_id_type:
            return vendor_id_type

    # Fall back to vendor-based classification
    if vendor:
        vendor_lower = vendor.lower()
        for pattern, device_type in VENDOR_PATTERNS:
            if pattern in vendor_lower:
                return device_type

    return TYPE_UNKNOWN


def get_type_icon(device_type: str) -> str:
    """Get the icon for a device type."""
    return TYPE_ICONS.get(device_type, TYPE_ICONS[TYPE_UNKNOWN])


def get_type_label(device_type: str) -> str:
    """Get the human-readable label for a device type."""
    return TYPE_LABELS.get(device_type, TYPE_LABELS[TYPE_UNKNOWN])


def get_all_types() -> list[tuple[str, str, str]]:
    """Get all device types with their icons and labels."""
    return [
        (dtype, TYPE_ICONS[dtype], TYPE_LABELS[dtype])
        for dtype in TYPE_LABELS.keys()
    ]
