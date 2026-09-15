"""Device type classification based on vendor and patterns."""

import re
from typing import Optional

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
            return TYPE_BEACON

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
) -> str:
    """
    Classify a device based on its vendor, name, service UUIDs, device
    class, and raw manufacturer data. Returns a device type constant.

    Priority: Manufacturer data > Service UUIDs > Name patterns > Device class > Vendor patterns
    """
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
