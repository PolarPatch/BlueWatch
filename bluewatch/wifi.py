"""Wi-Fi recognition: parse 802.11 management frames heard by a monitor-mode
adapter and pick out the few things worth keeping.

Listen-only, like everything else in BlueWatch: frames are read, never sent.
Only management-frame headers and information elements are looked at, never
data frames. And unlike Bluetooth, ordinary networks and phones are not
stored at all; only matches are (cameras, attack tools, drones), plus alerts
for attacks that are not a device (deauthentication floods, evil twins).

The capture side lives in wifi_sniffer.py. Everything here is pure and
testable without hardware.
"""

from __future__ import annotations

import json
import struct
import zlib
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from .classifier import DRONE_REMOTE_ID_SERVICE_DATA_UUID, DRONE_REMOTE_ID_AD_APP_CODE

# 802.11 management subtypes
SUBTYPE_PROBE_REQ = 4
SUBTYPE_PROBE_RESP = 5
SUBTYPE_BEACON = 8
SUBTYPE_DISASSOC = 10
SUBTYPE_DEAUTH = 12

IE_SSID = 0
IE_DS_PARAMS = 3
IE_RSN = 48
IE_PWNAGOTCHI = 222
IE_VENDOR = 221

# Tags stored in service_uuids for Wi-Fi devices; classifier.classify_wifi()
# maps them to a type.
TAG_PREFIX = "wifi-sig:"

# SSID prefixes, case-insensitive. Axon body cameras and Flock setup
# networks from SquachWatch-CYD (skizzophrenic) and Flock-You
# (colonelpanichacks, MIT); Pineapple and deauther are the tools' documented
# defaults.
SSID_PREFIXES = (
    ("ab2-", "axon-ssid", "Axon Body 2"),
    ("ab3-", "axon-ssid", "Axon Body 3"),
    ("ab4-", "axon-ssid", "Axon Body 4"),
    ("axon-", "axon-ssid", "Axon"),
    ("flock-", "flock-ssid", "Flock setup network"),
    ("pineapple_", "pineapple", "WiFi Pineapple"),
    ("pwned", "deauther", "ESP deauther"),
)
# A provisioned Flock camera's bare network name (Flock-You), exact.
SSID_EXACT = {"flock": ("flock-ssid", "Flock camera network")}

# Address blocks that name the maker. Generic module vendors (Liteon,
# Espressif, ...) that Flock also uses are not here: alone they would flag
# every gadget built on the same module.
OUI_TAGS = {
    "B4:1E:52": ("flock-oui", "Flock Safety"),
    "00:25:DF": ("axon-oui", "Axon"),
}
# Hak5 habits: locally administered, so anybody can use them. Only shown
# next to a Pineapple SSID, never a match alone.
HAK5_LA_OUIS = ("02:C0:CA", "02:13:37")

PWNAGOTCHI_BSSID = "DE:AD:BE:EF:DE:AD"
REMOTE_ID_OUI = bytes.fromhex("fa0bbc")
REMOTE_ID_VENDOR_TYPE = 0x0D


@dataclass
class Frame:
    subtype: int
    addr1: str
    addr2: str
    addr3: str
    rssi: Optional[int] = None
    channel: Optional[int] = None
    ssid: Optional[str] = None
    security: Optional[str] = None  # "open", "wep" or "protected"
    ies: list[tuple[int, bytes]] = field(default_factory=list)


@dataclass
class Hit:
    """Something worth storing as a device."""
    mac: str
    name: Optional[str]
    tags: list[str]
    rssi: Optional[int]
    state: dict
    service_data: Optional[dict] = None


@dataclass
class Event:
    """An attack that is not a device: shown as an alert."""
    kind: str  # "deauth_flood" or "evil_twin"
    key: str
    title: str
    message: str


def _mac(raw: bytes) -> str:
    return ":".join(f"{b:02X}" for b in raw)


def freq_to_channel(freq: Optional[int]) -> Optional[int]:
    if not freq:
        return None
    if freq == 2484:
        return 14
    if 2412 <= freq <= 2472:
        return (freq - 2407) // 5
    if 5000 <= freq <= 5900:
        return (freq - 5000) // 5
    if 5955 <= freq <= 7115:
        return (freq - 5950) // 5
    return None


# Radiotap fields up to antenna signal: (alignment, size)
_RADIOTAP_FIELDS = [(8, 8), (1, 1), (1, 1), (2, 4), (2, 2), (1, 1)]


def parse_radiotap(packet: bytes) -> Optional[tuple[Optional[int], Optional[int], bytes]]:
    """(rssi dBm, frequency MHz, 802.11 frame) from a radiotap packet."""
    if len(packet) < 8 or packet[0] != 0:
        return None
    length = struct.unpack_from("<H", packet, 2)[0]
    if length > len(packet) or length < 8:
        return None
    # The present words chain while bit 31 is set; fields start after them.
    words = []
    pos = 4
    while True:
        if pos + 4 > length:
            return None
        word = struct.unpack_from("<I", packet, pos)[0]
        words.append(word)
        pos += 4
        if not word & 0x80000000:
            break
    present = words[0]
    rssi = freq = None
    fcs = False
    for bit, (align, size) in enumerate(_RADIOTAP_FIELDS):
        if not present & (1 << bit):
            continue
        pos = (pos + align - 1) & ~(align - 1)
        if pos + size > length:
            break
        if bit == 1:
            fcs = bool(packet[pos] & 0x10)
        elif bit == 3:
            freq = struct.unpack_from("<H", packet, pos)[0]
        elif bit == 5:
            rssi = struct.unpack_from("<b", packet, pos)[0]
        pos += size
    frame = packet[length:]
    if fcs and len(frame) >= 4:
        frame = frame[:-4]
    return rssi, freq, frame


def _walk_ies(body: bytes) -> list[tuple[int, bytes]]:
    ies = []
    pos = 0
    while pos + 2 <= len(body):
        ie_id, ie_len = body[pos], body[pos + 1]
        if pos + 2 + ie_len > len(body):
            break
        ies.append((ie_id, body[pos + 2:pos + 2 + ie_len]))
        pos += 2 + ie_len
    return ies


def parse_frame(frame: bytes, rssi: Optional[int] = None, freq: Optional[int] = None) -> Optional[Frame]:
    """A management frame we care about, or None."""
    if len(frame) < 24:
        return None
    fc = frame[0]
    if (fc >> 2) & 0x3 != 0:  # management frames only
        return None
    subtype = (fc >> 4) & 0xF
    if subtype not in (SUBTYPE_PROBE_REQ, SUBTYPE_PROBE_RESP, SUBTYPE_BEACON, SUBTYPE_DISASSOC, SUBTYPE_DEAUTH):
        return None
    f = Frame(subtype=subtype, addr1=_mac(frame[4:10]), addr2=_mac(frame[10:16]),
              addr3=_mac(frame[16:22]), rssi=rssi, channel=freq_to_channel(freq))
    if subtype in (SUBTYPE_DEAUTH, SUBTYPE_DISASSOC):
        return f
    if subtype == SUBTYPE_PROBE_REQ:
        f.ies = _walk_ies(frame[24:])
    else:
        if len(frame) < 36:
            return None
        capability = struct.unpack_from("<H", frame, 34)[0]
        f.ies = _walk_ies(frame[36:])
        has_wpa = any(i == IE_RSN or (i == IE_VENDOR and d[:4] == b"\x00\x50\xf2\x01") for i, d in f.ies)
        f.security = "protected" if has_wpa else ("wep" if capability & 0x0010 else "open")
    for ie_id, data in f.ies:
        if ie_id == IE_SSID and f.ssid is None:
            ssid = data.decode("utf-8", errors="replace").replace("\x00", "")
            f.ssid = ssid if ssid.isprintable() else ssid.encode("unicode_escape").decode()
        elif ie_id == IE_DS_PARAMS and data:
            f.channel = data[0]
    return f


def pwnagotchi_info(f: Frame) -> Optional[dict]:
    """The JSON a Pwnagotchi announces about itself in IE 222, if any."""
    chunks = b"".join(d for i, d in f.ies if i == IE_PWNAGOTCHI)
    if not chunks:
        return None
    for decode in (lambda b: b, zlib.decompress, lambda b: zlib.decompress(b, 16 + zlib.MAX_WBITS)):
        try:
            info = json.loads(decode(chunks))
        except (ValueError, zlib.error):
            continue
        if isinstance(info, dict) and ("pwnd_tot" in info or "identity" in info or "name" in info):
            return info
    return None


def _clean(text, limit: int = 32) -> Optional[str]:
    if not isinstance(text, str):
        return None
    text = "".join(c for c in text if c.isprintable())[:limit].strip()
    return text or None


def remote_id_service_data(f: Frame) -> Optional[dict]:
    """A Remote ID beacon's messages, shaped like the Bluetooth service data
    classifier.decode_drone_remote_id() reads. A Location message wins, so
    the drone's position is what gets stored; otherwise the Basic ID."""
    for ie_id, data in f.ies:
        if ie_id != IE_VENDOR or data[:3] != REMOTE_ID_OUI or len(data) < 5 or data[3] != REMOTE_ID_VENDOR_TYPE:
            continue
        counter, body = data[4], data[5:]
        messages = []
        if body and body[0] >> 4 == 0xF and len(body) >= 3:  # message pack
            size, count = body[1], body[2]
            for n in range(count):
                start = 3 + n * size
                if size < 1 or start + size > len(body):
                    break
                messages.append(body[start:start + size])
        elif body:
            messages.append(body[:25])
        if not messages:
            return None
        messages.sort(key=lambda m: {1: 0, 0: 1}.get(m[0] >> 4, 2))
        return {DRONE_REMOTE_ID_SERVICE_DATA_UUID: bytes([DRONE_REMOTE_ID_AD_APP_CODE, counter]) + messages[0],
                "_uas_ids": [m[2:22].split(b"\x00", 1)[0].decode("ascii", "replace").strip()
                             for m in messages if m[0] >> 4 == 0 and len(m) >= 22]}
    return None


class WifiWatch:
    """Turns frames into hits and events. Keeps a little state for the
    attacks that only show up across frames."""

    DEAUTH_WINDOW = 10.0       # seconds
    DEAUTH_PER_SENDER = 30     # frames from one transmitter in the window; access
                               # points kicking clients (band steering, mesh) stay below
    EVENT_COOLDOWN = 900.0     # seconds before the same event fires again
    TWIN_WINDOW = 300.0        # an open and a protected copy within this long

    def __init__(self) -> None:
        self._deauth: dict[str, deque[float]] = {}
        self._ssids: dict[str, dict[str, tuple[str, float]]] = {}  # ssid -> bssid -> (security, when)
        self._fired: dict[str, float] = {}
        self.frames = 0
        self.beacons = 0
        self.deauths = 0

    def _fire(self, key: str, now: float) -> bool:
        if now - self._fired.get(key, -1e9) < self.EVENT_COOLDOWN:
            return False
        self._fired[key] = now
        return True

    def feed(self, f: Frame, now: float) -> tuple[Optional[Hit], Optional[Event]]:
        self.frames += 1
        if f.subtype in (SUBTYPE_DEAUTH, SUBTYPE_DISASSOC):
            self.deauths += 1
            return None, self._deauth_event(f, now)
        if f.subtype == SUBTYPE_PROBE_REQ:
            return None, None  # phones asking for networks: never stored
        self.beacons += 1
        return self._hit(f), self._twin_event(f, now)

    def _deauth_event(self, f: Frame, now: float) -> Optional[Event]:
        times = self._deauth.setdefault(f.addr2, deque())
        times.append(now)
        while times and now - times[0] > self.DEAUTH_WINDOW:
            times.popleft()
        if len(self._deauth) > 2000:
            for mac in [m for m, t in self._deauth.items() if not t or now - t[-1] > self.DEAUTH_WINDOW]:
                del self._deauth[mac]
        if len(times) < self.DEAUTH_PER_SENDER or not self._fire("deauth:" + f.addr2, now):
            return None
        target = "everyone on the network" if f.addr1 == "FF:FF:FF:FF:FF:FF" else f.addr1
        return Event("deauth_flood", f.addr2, "⚠ Wi-Fi deauthentication flood",
                     f"{len(times)} deauth/disassoc frames in {self.DEAUTH_WINDOW:.0f}s claiming to come from "
                     f"{f.addr2} (channel {f.channel or '?'}), aimed at {target}. Used to knock devices off "
                     "Wi-Fi, often to capture their reconnect.")

    def _twin_event(self, f: Frame, now: float) -> Optional[Event]:
        if not f.ssid or f.security is None:
            return None
        seen = self._ssids.setdefault(f.ssid, {})
        seen[f.addr3] = (f.security, now)
        for bssid in [b for b, (_, t) in seen.items() if now - t > self.TWIN_WINDOW]:
            del seen[bssid]
        if len(self._ssids) > 5000:
            for ssid in [s for s, b in self._ssids.items() if not b]:
                del self._ssids[ssid]
        kinds = {sec for sec, _ in seen.values()}
        if "open" in kinds and "protected" in kinds and self._fire("twin:" + f.ssid, now):
            open_ones = [b for b, (sec, _) in seen.items() if sec == "open"]
            return Event("evil_twin", f.ssid, "⚠ Possible evil twin Wi-Fi",
                         f"\"{f.ssid}\" is broadcast both with a password and open, from {len(seen)} access "
                         f"points (open: {', '.join(open_ones[:3])}). An open copy of a protected network is "
                         "a classic trap for devices that join by name.")
        return None

    def _hit(self, f: Frame) -> Optional[Hit]:
        bssid = f.addr3 if f.subtype == SUBTYPE_BEACON else f.addr2
        tags: list[str] = []
        evidence: list[str] = []
        name = f.ssid or None
        state: dict = {"ssid": f.ssid or "(hidden)", "channel": f.channel, "security": f.security}
        service_data = None

        info = pwnagotchi_info(f)
        if info is not None or bssid == PWNAGOTCHI_BSSID and f.ies and any(i == IE_PWNAGOTCHI for i, _ in f.ies):
            info = info or {}
            tags.append("pwnagotchi")
            evidence.append("Pwnagotchi beacon")
            name = _clean(info.get("name")) or "Pwnagotchi"
            if isinstance(info.get("pwnd_tot"), int):
                state["handshakes"] = info["pwnd_tot"]
            if _clean(info.get("version")):
                state["version"] = _clean(info.get("version"))

        rid = remote_id_service_data(f)
        if rid:
            uas_ids = [u for u in rid.pop("_uas_ids") if u]
            service_data = rid
            tags.append("remote-id")
            evidence.append("Remote ID beacon")
            name = _clean(uas_ids[0]) if uas_ids else (name or "Drone")

        lssid = (f.ssid or "").lower()
        for prefix, tag, label in SSID_PREFIXES:
            if lssid.startswith(prefix):
                tags.append(tag)
                evidence.append(label + " SSID")
                break
        else:
            if lssid in SSID_EXACT:
                tag, label = SSID_EXACT[lssid]
                tags.append(tag)
                evidence.append(label)
        oui = bssid[:8]
        if oui in OUI_TAGS:
            tag, label = OUI_TAGS[oui]
            tags.append(tag)
            evidence.append(label + " OUI")
        if "pineapple" in tags and oui in HAK5_LA_OUIS:
            evidence.append("Hak5 address habit")

        if not tags:
            return None
        state["evidence"] = ", ".join(evidence)
        return Hit(mac=bssid, name=name, tags=[TAG_PREFIX + t for t in tags], rssi=f.rssi,
                   state={k: v for k, v in state.items() if v is not None}, service_data=service_data)
