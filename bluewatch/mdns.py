"""Discovery of devices on the local network via mDNS (Bonjour / Avahi).

Bluetooth only sees devices that advertise over Bluetooth. Many household
devices (printers, TVs, speakers, computers, smart-home hubs) also announce
themselves on the LAN with their own name and model, which is a strong,
self-declared identity that BLE alone often lacks.

Adapted from Neighborhood Rhythm (https://github.com/siropkin/neighborhood-rhythm,
MIT licensed, (c) Ivan Seredkin): the list of service types worth browsing,
the TXT-record fields that carry the model, and the HomeKit category table.
See CREDITS.md. Rewritten here for BlueWatch's asyncio daemon.

mDNS devices have no Bluetooth address, so they are keyed by their mDNS
hostname (e.g. "Living-room-TV.local"). Everything is passive: only standard
multicast service queries are sent, nothing connects to the devices.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Service types that carry useful identity data. Browsed explicitly rather
# than through a meta-query: faster, and these are the ones we can classify.
MDNS_TYPES = [
    "_airplay._tcp.local.", "_googlecast._tcp.local.", "_raop._tcp.local.",
    "_spotify-connect._tcp.local.", "_hap._tcp.local.", "_ipp._tcp.local.",
    "_smb._tcp.local.", "_ssh._tcp.local.", "_esphome._tcp.local.",
    "_yandexio._tcp.local.",
]

# HomeKit accessory category ids (the `ci` TXT field of _hap, per the HomeKit
# Accessory Protocol spec) -> category name. Only ids that are certain.
HAP_CATEGORY = {
    2: "bridge", 3: "fan", 5: "light", 6: "lock", 7: "outlet", 8: "switch",
    9: "thermostat", 10: "sensor", 17: "camera", 18: "camera", 24: "tv",
    26: "speaker", 31: "tv", 33: "router",
}

# Which TXT key holds the model, per service type. NOT the same everywhere:
# in _raop, `md` is the supported *metadata types* ("0,1,2"), not a model.
_MODEL_KEYS = {
    "_airplay._tcp": ("model",),
    "_raop._tcp": ("am",),
    "_googlecast._tcp": ("md",),
    "_ipp._tcp": ("ty", "usb_MDL"),
    "_hap._tcp": ("md",),
}


@dataclass
class MdnsDevice:
    key: str                       # hostname, e.g. "Living-room-TV.local"
    label: str                     # display name
    services: list = field(default_factory=list)   # e.g. ["_airplay._tcp", "hap-category:light"]
    addresses: list = field(default_factory=list)
    model: Optional[str] = None
    category: Optional[str] = None


def _short_service(service_type: str) -> str:
    return service_type.removesuffix(".local.").removesuffix(".")


def _instance_name(name: str, service_type: str) -> str:
    name = name.removesuffix("." + service_type)
    # AirPlay audio (RAOP) instance names look like "AABBCCDDEEFF@Room".
    if "@" in name:
        name = name.split("@", 1)[1]
    return name.strip()


def _merge(resolved: list) -> list:
    """Merge every resolved (service_type, name, info) triple of the same
    host into one device, so a device announcing several services is one row."""
    hosts: dict = {}
    for service_type, name, info in resolved:
        hostname = (info.server or "").rstrip(".")
        if not hostname:
            continue
        entry = hosts.setdefault(hostname, {
            "names": [], "services": set(), "addresses": set(),
            "model": None, "category": None,
        })
        instance = _instance_name(name, service_type)
        if instance:
            entry["names"].append(instance)
        entry["services"].add(_short_service(service_type))
        try:
            entry["addresses"].update(info.parsed_addresses())
        except Exception:
            pass
        txt = info.decoded_properties or {}
        if not entry["model"]:
            for key in _MODEL_KEYS.get(_short_service(service_type), ()):
                if txt.get(key):
                    entry["model"] = str(txt[key])
                    break
        ci = txt.get("ci")
        if not entry["category"] and ci and str(ci).isdigit():
            entry["category"] = HAP_CATEGORY.get(int(ci))

    devices = []
    for hostname, entry in sorted(hosts.items()):
        name = min(entry["names"], key=len) if entry["names"] else hostname.removesuffix(".local")
        model = entry["model"]
        label = f"{name} ({model})" if model and model.lower() not in name.lower() else name
        services = sorted(entry["services"])
        if entry["category"]:
            services.append(f"hap-category:{entry['category']}")
        devices.append(MdnsDevice(
            key=hostname, label=label, services=services,
            addresses=sorted(entry["addresses"]),
            model=model, category=entry["category"],
        ))
    return devices


class MdnsScanner:
    """Periodic mDNS sweep. `scan()` browses for a few seconds and returns
    every device that answered."""

    def __init__(self, listen_time: float = 8.0):
        self._listen_time = listen_time
        self._azc = None

    async def start(self) -> bool:
        """Open the multicast socket. Returns False (and logs) if mDNS can't
        be used, so the rest of BlueWatch carries on without it."""
        try:
            from zeroconf.asyncio import AsyncZeroconf
        except ImportError:
            logger.info("mDNS discovery unavailable: the 'zeroconf' package is not installed")
            return False
        try:
            self._azc = AsyncZeroconf()
        except OSError as e:
            logger.warning(f"mDNS discovery unavailable: {e}")
            return False
        return True

    async def stop(self) -> None:
        if self._azc is not None:
            await self._azc.async_close()
            self._azc = None

    async def scan(self) -> list:
        if self._azc is None:
            return []
        from zeroconf import ServiceStateChange
        from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo

        found: set = set()

        def on_change(zeroconf, service_type, name, state_change):
            if state_change is not ServiceStateChange.Removed:
                found.add((service_type, name))

        browser = AsyncServiceBrowser(self._azc.zeroconf, MDNS_TYPES, handlers=[on_change])
        try:
            await asyncio.sleep(self._listen_time)
        finally:
            await browser.async_cancel()

        async def resolve(service_type, name):
            info = AsyncServiceInfo(service_type, name)
            try:
                if await info.async_request(self._azc.zeroconf, 2000):
                    return service_type, name, info
            except Exception as e:
                logger.debug(f"mDNS resolve failed for {name}: {e}")
            return None

        results = await asyncio.gather(*(resolve(t, n) for t, n in found))
        return _merge([r for r in results if r])
