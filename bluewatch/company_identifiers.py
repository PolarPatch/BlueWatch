"""Bluetooth SIG company identifier lookup -- company ID -> company name.

Every BLE manufacturer-specific advertisement (AD type 0xFF) leads with a
2-byte company ID assigned by the Bluetooth SIG, identifying who made the
chipset/firmware sending it (e.g. 0x004C = Apple, 0x0075 = Samsung). This
module resolves that ID against a bundled snapshot of the SIG's own
public registry (~4,000 assigned companies), giving BlueWatch a real
vendor name straight from a device's own broadcast -- notably useful for
a device with a randomized (privacy) MAC address, where the usual
OUI-based vendor lookup (scanner.py's _get_vendor) has nothing real to
go on, since a randomized MAC's first three bytes say nothing about the
actual manufacturer.

This is a much weaker signal than the specific per-vendor fingerprints
elsewhere in classifier.py (a company ID only says who made the radio
chip/stack, not what kind of product it's in -- the same company ID can
appear on phones, earbuds, and smart-home gadgets alike from one large
vendor), so it's used strictly as a vendor-name fallback (fills the
`vendor` field only when otherwise empty), never for device-type
classification.

Data source: assigned_numbers/company_identifiers/company_identifiers.yaml
from https://bitbucket.org/bluetooth-SIG/public (Bluetooth SIG's own
public assigned-numbers repository). Bundled as a static snapshot
(bluewatch/data/company_identifiers.csv, converted from that YAML) so
this works offline and doesn't depend on a live fetch from bitbucket.org
at runtime.
"""

import csv
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

COMPANY_IDS_CSV = Path(__file__).resolve().parent / "data" / "company_identifiers.csv"


def _load_companies() -> dict:
    companies = {}
    if not COMPANY_IDS_CSV.exists():
        logger.warning(f"Bluetooth company identifier database not found at {COMPANY_IDS_CSV}")
        return companies
    try:
        with open(COMPANY_IDS_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                raw_id = (row.get("Company ID") or "").strip()
                name = (row.get("Company Name") or "").strip()
                if not raw_id.lower().startswith("0x") or not name:
                    continue
                try:
                    company_id = int(raw_id, 16)
                except ValueError:
                    continue
                companies[company_id] = name
    except (OSError, csv.Error) as e:
        logger.warning(f"Could not read Bluetooth company identifier database: {e}")
        return {}
    logger.info(f"Loaded {len(companies)} Bluetooth SIG company identifier entries")
    return companies


_COMPANIES = _load_companies()


def lookup_company_name(company_id: int) -> Optional[str]:
    """Company name for a Bluetooth SIG-assigned company ID, or None if
    unassigned/not in the bundled snapshot."""
    return _COMPANIES.get(company_id)


def vendor_from_manufacturer_data(manufacturer_data: Optional[dict]) -> Optional[str]:
    """Resolve a vendor name from the company ID(s) present in a device's
    manufacturer_data, for use as a fallback when MAC-OUI vendor lookup
    comes up empty (typically a randomized/privacy MAC). Returns the
    first resolvable company name found, or None."""
    if not manufacturer_data:
        return None
    for company_id in manufacturer_data:
        name = _COMPANIES.get(company_id)
        if name:
            return name
    return None
