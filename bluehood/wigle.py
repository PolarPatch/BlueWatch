"""Vendor/name lookup for a specific MAC against WiGLE.net's crowdsourced
Bluetooth database (api.wigle.net).

Deliberately narrow: this only ever reads the device's recorded name/type
from a WiGLE search result to fill in a vendor we couldn't otherwise
identify. It never reads, logs, or stores the location fields WiGLE also
returns (trilat/trilong/lastupdt and similar) -- pulling another device's
sighting history/location trail from a third-party database is a form of
tracking that's out of scope for BlueWatch, which stays passive and local.
"""

import logging
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

WIGLE_BT_SEARCH_URL = "https://api.wigle.net/api/v2/bluetooth/search"


async def lookup_vendor(mac: str, api_name: str, api_token: str) -> Optional[str]:
    """Look up a single MAC against WiGLE's Bluetooth database.

    Returns a vendor/name string if WiGLE has a record with a non-empty
    name for this exact address, else None (not found, no credentials,
    rate-limited, or any request error -- all treated the same way: no
    vendor learned this time, try again another day).
    """
    if not api_name or not api_token:
        return None

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                WIGLE_BT_SEARCH_URL,
                params={"netid": mac},
                auth=aiohttp.BasicAuth(api_name, api_token),
                headers={"Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 429:
                    logger.warning("WiGLE lookup rate-limited")
                    return None
                if response.status != 200:
                    logger.debug(f"WiGLE lookup HTTP {response.status} for {mac}")
                    return None
                data = await response.json()
    except Exception as e:
        logger.debug(f"WiGLE lookup error for {mac}: {e}")
        return None

    if not data.get("success"):
        return None

    results = data.get("results") or []
    if not results:
        return None

    # Only ever read the name -- explicitly not trilat/trilong/lastupdt/etc.
    name = (results[0].get("name") or "").strip()
    return name or None
