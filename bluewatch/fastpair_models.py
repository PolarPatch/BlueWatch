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
