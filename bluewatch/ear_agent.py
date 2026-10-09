"""bluewatch-ear: turn a spare Linux box with Bluetooth into a remote ear.

Listens passively with bleak and posts what it heard to a BlueWatch hub every
few seconds (see ears.py for the wire format). No database, no web UI, no
connecting to devices -- just ears. Needs Linux/BlueZ: macOS hides real
Bluetooth addresses behind per-host UUIDs, which a hub cannot match.

    bluewatch-ear --hub http://192.0.2.10:8080 --token bwear_... --name "Garage"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import platform
import random
import signal
import socket
import time
from typing import Optional

import aiohttp
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from . import __version__
from .ears import MAX_HEARD_PER_BATCH, PROTOCOL_VERSION

logger = logging.getLogger("bluewatch.ear")

SEND_INTERVAL = 5.0
MAX_PENDING = 4000          # distinct addresses kept between sends
MAX_UNSENT_AGE = 45.0       # drop what could not be delivered in time


class Ear:
    def __init__(self, hub: str, token: str, name: str, adapter: Optional[str]) -> None:
        self.url = hub.rstrip("/")
        self.token = token
        self.name = name
        self.adapter = adapter
        # address -> latest observation since the last successful send
        self.pending: dict[str, dict] = {}
        self.sent_total = 0
        self.failures = 0
        self.stopping = asyncio.Event()

    def _on_advert(self, device: BLEDevice, adv: AdvertisementData) -> None:
        mac = device.address.upper()
        if mac not in self.pending and len(self.pending) >= MAX_PENDING:
            return
        item = {"mac": mac, "rssi": adv.rssi, "at": time.time(), "by": self.name}
        name = adv.local_name or device.name
        if name and name.replace("-", ":").upper() != mac:
            item["name"] = name[:64]
        if adv.tx_power is not None:
            item["tx"] = adv.tx_power
        if adv.manufacturer_data:
            item["m"] = {str(k): bytes(v).hex() for k, v in list(adv.manufacturer_data.items())[:8]}
        if adv.service_uuids:
            item["u"] = list(adv.service_uuids)[:24]
        if adv.service_data:
            item["s"] = {k: bytes(v).hex() for k, v in list(adv.service_data.items())[:8]}
        self.pending[mac] = item

    async def _hello(self, session: aiohttp.ClientSession) -> None:
        while not self.stopping.is_set():
            try:
                async with session.get(self.url + "/api/ears/v1/hello") as response:
                    data = await response.json(content_type=None)
                    if response.status == 200:
                        logger.info(f"Connected to BlueWatch {data.get('bluewatch')} as ear "
                                    f"'{data['ear']['name']}', listening as '{self.name}'")
                        return
                    logger.error(f"Hub refused this ear: {data.get('error', response.status)}")
                    if response.status in (401, 403):
                        raise SystemExit(2)
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
                logger.warning(f"Hub not reachable yet ({e}); retrying")
            await asyncio.sleep(15)

    async def _send(self, session: aiohttp.ClientSession) -> None:
        now = time.time()
        batch = [item for item in self.pending.values() if now - item["at"] <= MAX_UNSENT_AGE]
        if not batch:
            self.pending.clear()
            return
        batch.sort(key=lambda item: item["at"], reverse=True)
        batch = batch[:MAX_HEARD_PER_BATCH]
        sent_macs = {item["mac"]: item["at"] for item in batch}
        payload = {"v": PROTOCOL_VERSION, "sent": time.time(),
                   "software": f"bluewatch-ear {__version__}", "heard": batch}
        async with session.post(self.url + "/api/ears/v1/heard", data=json.dumps(payload),
                                headers={"Content-Type": "application/json"}) as response:
            data = await response.json(content_type=None)
            if response.status in (401, 403):
                logger.error(f"Hub refused this ear: {data.get('error')}")
                raise SystemExit(2)
            if response.status != 200:
                raise aiohttp.ClientError(f"HTTP {response.status}: {data.get('error')}")
        # Only forget what was delivered and has not been heard again since.
        for mac, at in sent_macs.items():
            if self.pending.get(mac, {}).get("at") == at:
                del self.pending[mac]
        for mac in [m for m, item in self.pending.items() if now - item["at"] > MAX_UNSENT_AGE]:
            del self.pending[mac]
        self.sent_total += data.get("taken", 0)

    async def run(self) -> None:
        headers = {"Authorization": "Bearer " + self.token,
                   "User-Agent": f"bluewatch-ear/{__version__}"}
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            await self._hello(session)
            # Report every advert, not only changed ones, so a device that
            # sits still keeps being heard.
            kwargs = {"detection_callback": self._on_advert,
                      "bluez": {"filters": {"DuplicateData": True}}}
            if self.adapter:
                kwargs["adapter"] = self.adapter
            scanner = BleakScanner(**kwargs)
            await scanner.start()
            logger.info(f"Listening, sending to the hub every {SEND_INTERVAL:.0f}s")
            last_report = time.monotonic()
            try:
                while not self.stopping.is_set():
                    delay = SEND_INTERVAL if not self.failures else min(60, 2 ** self.failures) + random.random()
                    try:
                        await asyncio.wait_for(self.stopping.wait(), timeout=delay)
                    except asyncio.TimeoutError:
                        pass
                    try:
                        await self._send(session)
                        self.failures = 0
                    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
                        self.failures = min(self.failures + 1, 6)
                        logger.warning(f"Send failed ({e}); keeping {len(self.pending)} addresses for retry")
                    if time.monotonic() - last_report > 300:
                        last_report = time.monotonic()
                        logger.info(f"{self.sent_total} adverts delivered so far, "
                                    f"{len(self.pending)} waiting")
            finally:
                await scanner.stop()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bluewatch-ear",
        description="Listen for Bluetooth LE advertisements and report them to a BlueWatch hub.")
    parser.add_argument("--hub", required=True, help="BlueWatch address, e.g. http://192.0.2.10:8080")
    parser.add_argument("--token", required=True, help="ear token from BlueWatch Config > Ears")
    parser.add_argument("--name", default=socket.gethostname(),
                        help="listener name shown in BlueWatch (default: hostname)")
    parser.add_argument("--adapter", help="Bluetooth adapter, e.g. hci1 (default: system default)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    if platform.system() == "Darwin":
        parser.error("macOS hides real Bluetooth addresses, so it cannot be an ear. Use Linux.")

    ear = Ear(args.hub, args.token, args.name[:48], args.adapter)
    loop = asyncio.new_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, ear.stopping.set)
    try:
        loop.run_until_complete(ear.run())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
