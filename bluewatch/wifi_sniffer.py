"""Optional Wi-Fi ears: read 802.11 management frames from a monitor-mode
adapter (Linux) or replay a capture file, and hand them to wifi.py.

Off unless asked for, with BLUEWATCH_WIFI_IFACE / --wifi-iface (a USB
adapter that can do monitor mode, e.g. MediaTek mt76; the Raspberry Pi's own
Wi-Fi cannot) or BLUEWATCH_WIFI_PCAP / --wifi-pcap (a radiotap capture, for
trying it out without hardware). Never transmits: the adapter is only put in
monitor mode and tuned from channel to channel.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
import struct
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Optional

from . import wifi

logger = logging.getLogger(__name__)

ETH_P_ALL = 0x0003
DEFAULT_CHANNELS = list(range(1, 14))   # 2.4 GHz, Europe
DWELL_SECONDS = 0.25                    # a few beacon intervals per channel
LINKTYPE_IEEE802_11 = 105
LINKTYPE_RADIOTAP = 127

# Read by the web server's /api/wifi.
STATUS: dict = {"enabled": False, "source": None, "state": "off", "error": None,
                "channel": None, "frames": 0, "beacons": 0, "deauths": 0, "hits": 0,
                "events": []}


def channels_from_env() -> list[int]:
    raw = os.environ.get("BLUEWATCH_WIFI_CHANNELS", "")
    chans = [int(c) for c in raw.replace(" ", "").split(",") if c.isdigit()]
    return chans or DEFAULT_CHANNELS


async def _run(*cmd: str) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    out, _ = await proc.communicate()
    return proc.returncode, out.decode(errors="replace").strip()


async def _iface_type(iface: str) -> Optional[str]:
    code, out = await _run("iw", "dev", iface, "info")
    if code != 0:
        return None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("type "):
            return line.split()[1]
    return None


async def _carries_default_route(iface: str) -> bool:
    try:
        for line in Path("/proc/net/route").read_text().splitlines()[1:]:
            parts = line.split()
            if len(parts) > 2 and parts[0] == iface and parts[1] == "00000000":
                return True
    except OSError:
        pass
    return False


async def prepare_monitor(iface: str) -> None:
    """Put the adapter in monitor mode, unless it already is. Refuses the
    interface this machine is online through."""
    kind = await _iface_type(iface)
    if kind is None:
        raise RuntimeError(f"no Wi-Fi interface called {iface} (iw dev {iface} info failed)")
    if kind == "monitor":
        return
    if await _carries_default_route(iface):
        raise RuntimeError(f"{iface} carries this machine's network connection; use a second adapter")
    for cmd in (("ip", "link", "set", iface, "down"),
                ("iw", "dev", iface, "set", "type", "monitor"),
                ("ip", "link", "set", iface, "up")):
        code, out = await _run(*cmd)
        if code != 0:
            raise RuntimeError(f"{' '.join(cmd)} failed: {out or code} (does the adapter support monitor mode?)")
    logger.info(f"Wi-Fi: {iface} is in monitor mode")


async def _hop(iface: str, channels: list[int]) -> None:
    bad: set[int] = set()
    while True:
        for ch in channels:
            if ch in bad:
                continue
            code, out = await _run("iw", "dev", iface, "set", "channel", str(ch))
            if code != 0:
                bad.add(ch)
                logger.info(f"Wi-Fi: {iface} cannot tune to channel {ch}, skipping it ({out})")
                continue
            STATUS["channel"] = ch
            await asyncio.sleep(DWELL_SECONDS)
        if len(bad) == len(channels):
            raise RuntimeError(f"{iface} could not tune to any of channels {channels}")


async def frames_from_iface(iface: str, channels: list[int]) -> AsyncIterator[wifi.Frame]:
    await prepare_monitor(iface)
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
    sock.bind((iface, 0))
    sock.setblocking(False)
    hopper = asyncio.create_task(_hop(iface, channels))
    loop = asyncio.get_running_loop()
    try:
        while True:
            if hopper.done():
                hopper.result()  # raises what stopped it
            packet = await loop.sock_recv(sock, 4096)
            parsed = wifi.parse_radiotap(packet)
            if parsed is None:
                continue
            frame = wifi.parse_frame(parsed[2], parsed[0], parsed[1])
            if frame is not None:
                yield frame
    finally:
        hopper.cancel()
        sock.close()


def read_pcap(path: str):
    """Yield (timestamp, frame) from a pcap of radiotap or bare 802.11 frames."""
    with open(path, "rb") as fh:
        header = fh.read(24)
        if len(header) < 24:
            raise ValueError("not a pcap file")
        magic = header[:4]
        if magic in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1"):
            endian = "<"
        elif magic in (b"\xa1\xb2\xc3\xd4", b"\xa1\xb2\x3c\x4d"):
            endian = ">"
        else:
            raise ValueError("not a pcap file (pcapng is not supported; save as pcap)")
        nano = magic in (b"\x4d\x3c\xb2\xa1", b"\xa1\xb2\x3c\x4d")
        linktype = struct.unpack(endian + "I", header[20:24])[0]
        if linktype not in (LINKTYPE_RADIOTAP, LINKTYPE_IEEE802_11):
            raise ValueError(f"pcap link type {linktype} is not 802.11 (need radiotap, 127, or 802.11, 105)")
        while True:
            rec = fh.read(16)
            if len(rec) < 16:
                return
            sec, frac, incl, _ = struct.unpack(endian + "IIII", rec)
            data = fh.read(incl)
            if len(data) < incl:
                return
            ts = sec + frac / (1e9 if nano else 1e6)
            if linktype == LINKTYPE_RADIOTAP:
                parsed = wifi.parse_radiotap(data)
                if parsed is None:
                    continue
                frame = wifi.parse_frame(parsed[2], parsed[0], parsed[1])
            else:
                frame = wifi.parse_frame(data)
            if frame is not None:
                yield ts, frame


async def frames_from_pcap(path: str) -> AsyncIterator[tuple[float, wifi.Frame]]:
    """Replay a capture with its own timing squeezed 20x, so it ends."""
    first_ts = start = None
    for ts, frame in read_pcap(path):
        if first_ts is None:
            first_ts, start = ts, time.monotonic()
        delay = (ts - first_ts) / 20 - (time.monotonic() - start)
        if delay > 0:
            await asyncio.sleep(min(delay, 2.0))
        yield ts, frame


def note_event(event: wifi.Event) -> None:
    STATUS["events"] = ([{"kind": event.kind, "key": event.key, "title": event.title,
                          "message": event.message, "at": time.time()}] + STATUS["events"])[:20]
