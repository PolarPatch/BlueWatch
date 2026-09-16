"""Google Fast Pair Model ID lookup -- passive device identification.

Every Fast Pair accessory broadcasts its 3-byte Model ID in plain sight,
in its advertisement's service_data under service UUID 0xFE2C -- no
connection, no crypto, no API key needed to read it (unlike
fastpair.py's anti-spoof verification, which is a separate, unrelated
feature). This module resolves that Model ID against a bundled snapshot
of Google's public Fast Pair Model registry, giving an exact device
name/manufacturer/category for ~2800 real-world accessories for free.

Data source: bluewatch/data/fastpair_model_ids.csv, harvested by the
KULeuven-COSIC WhisperPair academic research project
(https://github.com/KULeuven-COSIC/WhisperPair), licensed CC-BY-4.0.
Bundled as a static snapshot (no runtime network fetch) so this works
offline and doesn't depend on that repo staying up.
"""

import csv
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MODEL_IDS_CSV = Path(__file__).resolve().parent / "data" / "fastpair_model_ids.csv"

# Google's Fast Pair DeviceType values as they appear in the source CSV --
# most rows use the string enum name, but a handful of newer/rarer
# categories only ever appear as their raw numeric enum ordinal (no string
# label in this export). Those numeric codes were identified by inspecting
# representative rows (e.g. every Device type=11 row is a "Tag"/"Finder"
# product with Supports tracking=TRUE; every Device type=13 row is a phone
# model like "Galaxy S23 Ultra"), not guessed blind. The actual mapping to
# BlueWatch's TYPE_* constants lives in classifier.py (this module stays
# free of that dependency to avoid a circular import, since classifier.py
# is the one that imports from here) -- see FASTPAIR_DEVICE_TYPE_MAP there.
# Known numeric codes, for reference: 10=Glasses, 11=Tag/Tracker,
# 12=Computer (Chromebook/box/base), 13=Phone, 16=Photo printer, 17=Mouse/HID.


def _load_models() -> dict:
    models = {}
    if not MODEL_IDS_CSV.exists():
        logger.warning(f"Fast Pair model database not found at {MODEL_IDS_CSV}")
        return models
    try:
        with open(MODEL_IDS_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                raw_id = (row.get("Model ID") or "").strip()
                if not raw_id.isdigit():
                    continue
                model_id_hex = format(int(raw_id), "06x")
                name = (row.get("Device name") or "").strip()
                if not name:
                    continue
                models[model_id_hex] = {
                    "name": name,
                    "manufacturer": (row.get("Manufacturer") or "").strip() or None,
                    "device_type_raw": (row.get("Device type") or "").strip() or None,
                }
    except (OSError, csv.Error) as e:
        logger.warning(f"Could not read Fast Pair model database: {e}")
        return {}
    logger.info(f"Loaded {len(models)} Fast Pair model entries")
    return models


_MODELS = _load_models()


def model_id_from_service_data(service_data: Optional[dict]) -> Optional[str]:
    """Extract Fast Pair's 3-byte Model ID (hex string) from a device's
    stored service_data dict, if present under the Fast Pair service UUID."""
    if not service_data:
        return None
    for key, value in service_data.items():
        normalized = key.lower().replace("-", "")
        if normalized.startswith("0000fe2c") and len(value) == 3:
            return value.hex()
    return None


def lookup_fastpair_model(model_id_hex: str) -> Optional[dict]:
    """Look up a Model ID hex string against the bundled registry.

    Returns {"name", "manufacturer", "device_type_raw"} or None if this
    Model ID isn't in the (necessarily incomplete) snapshot.
    """
    return _MODELS.get(model_id_hex.lower())


def identify_fastpair_device(service_data: Optional[dict]) -> Optional[dict]:
    """One-shot: extract the Model ID from service_data and resolve it.
    Returns the same shape as lookup_fastpair_model(), or None."""
    model_id_hex = model_id_from_service_data(service_data)
    if not model_id_hex:
        return None
    return lookup_fastpair_model(model_id_hex)


def _fe2c_payload(service_data: Optional[dict]) -> Optional[bytes]:
    """Raw bytes of the 0xFE2C service_data payload, any length -- unlike
    model_id_from_service_data(), which only matches the bare 3-byte
    discoverable-Model-ID form."""
    if not service_data:
        return None
    for key, value in service_data.items():
        if key.lower().replace("-", "").startswith("0000fe2c"):
            return value
    return None


# Fast Pair's non-discoverable "Account Advertising" payload (already-
# paired devices continuing to broadcast) can carry an optional Battery
# Notification extension after the Account Key filter and Salt TLVs.
# Byte layout verified against Google's own spec
# (https://developers.google.com/nearby/fast-pair/specifications/extensions/battery-notification)
# and cross-checked against blesploit/device-library's
# protocols/fast_pair/observer/adv_decode.lua (enrich_account_adv()),
# which parses this exact TLV chain byte-for-byte:
#   byte 0: version/flags (unused here)
#   byte 1: Account Key filter header -- high nibble = filter length in
#     octets, low nibble = filter type
#   next `filter_len` bytes: Account Key filter (bloom filter, ignored)
#   next byte: Salt TLV header -- high nibble = salt length, low nibble
#     = salt type
#   next `salt_len` bytes: salt value (ignored)
#   next byte (if present): Battery Notification header -- high nibble =
#     number of battery octets that follow, low nibble = notification type
#   next N bytes: one octet per component, in order left earbud/right
#     earbud/case -- each `0bSVVVVVVV`: high bit = charging, low 7 bits =
#     battery percentage (0-100), 127 = component not present/unknown.
_FASTPAIR_BATTERY_LABELS = ["left", "right", "case"]


def decode_fastpair_battery(service_data: Optional[dict]) -> Optional[dict]:
    """Decode the optional Battery Notification extension from a Fast
    Pair Account Advertising payload. Returns e.g.
    {"left": {"charging": bool, "pct": int|None}, "right": {...}, ...}
    (only components actually present), or None if there's no 0xFE2C
    service_data, it's the bare 3-byte Model ID form (no battery data
    possible), or the payload is too short to carry a battery section.

    Live/transient -- caller should recompute this on every sighting
    rather than caching it, battery level and charging state change over
    time."""
    payload = _fe2c_payload(service_data)
    if not payload or len(payload) <= 3:
        return None

    filter_len = (payload[1] >> 4) & 0x0F
    salt_header_idx = 2 + filter_len
    if salt_header_idx >= len(payload):
        return None
    salt_len = (payload[salt_header_idx] >> 4) & 0x0F
    battery_header_idx = salt_header_idx + 1 + salt_len
    if battery_header_idx >= len(payload):
        return None

    num_components = (payload[battery_header_idx] >> 4) & 0x0F
    if num_components == 0 or battery_header_idx + num_components >= len(payload):
        return None

    result = {}
    for i in range(num_components):
        octet = payload[battery_header_idx + 1 + i]
        charging = bool(octet & 0x80)
        pct = octet & 0x7F
        label = _FASTPAIR_BATTERY_LABELS[i] if i < len(_FASTPAIR_BATTERY_LABELS) else f"component_{i}"
        result[label] = {"charging": charging, "pct": None if pct == 127 else pct}

    return result or None
