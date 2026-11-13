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
import time
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
IE_INTERWORKING = 107
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
    # Setup networks (Fieldwatch catalog 111): an ExpressLRS RC link or
    # backpack, and an EZVIZ home camera waiting to be set up.
    ("expresslrs", "elrs-ssid", "ExpressLRS setup network"),
    ("ezviz_", "ezviz-ssid", "EZVIZ camera setup network"),
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
# French Direct Remote ID (arrete du 27 decembre 2019): OUI 6A:5C:35, type 1,
# big-endian TLVs. DJI's older DroneID beacon: OUI 26:37:12 (names the maker,
# position not decoded). Source: OffGridPete/Fieldwatch v1.1.44.
FRENCH_RID_OUI = bytes.fromhex("6a5c35")
DJI_DRONEID_OUI = bytes.fromhex("263712")
WFA_OUI = bytes.fromhex("506f9a")
MS_OUI = bytes.fromhex("0050f2")

# Standard elements carried under a vendor OUI: not products.
_STANDARD_VENDOR_IES = {
    (MS_OUI, 1): "WPA", (MS_OUI, 2): "WMM", (MS_OUI, 4): "WPS",
    (WFA_OUI, 0x09): "Wi-Fi Direct", (WFA_OUI, 0x0A): "Miracast", (WFA_OUI, 0x10): "Hotspot 2.0",
    (WFA_OUI, 0x16): "MBO-OCE", (WFA_OUI, 0x1B): "EasyMesh", (WFA_OUI, 0x1C): "OWE transition",
}

_ACCESS_NETWORK_TYPES = {
    0: "private", 1: "private with guest access", 2: "chargeable public", 3: "free public",
    4: "personal device", 5: "emergency services only", 14: "test", 15: "wildcard",
}
_VENUE_GROUPS = {
    1: "Assembly", 2: "Business", 3: "Educational", 4: "Factory/industrial", 5: "Institutional",
    6: "Mercantile", 7: "Residential", 8: "Storage", 9: "Utility", 10: "Vehicular", 11: "Outdoor",
}
_VENUE_TYPES = {
    (1, 3): "passenger terminal", (1, 10): "restaurant", (1, 12): "bar", (1, 13): "coffee shop",
    (2, 3): "fire station", (2, 4): "police station", (5, 1): "hospital", (5, 5): "prison",
    (6, 1): "retail store", (6, 5): "gas station", (7, 1): "private residence", (7, 2): "hotel",
    (10, 1): "car or truck", (10, 2): "airplane", (10, 3): "bus", (10, 4): "ferry",
    (10, 5): "ship or boat", (10, 6): "train", (10, 7): "motorbike", (11, 5): "bus stop",
}


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
    kind: str  # "deauth_flood", "evil_twin" or "trusted_network"
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


def interworking_info(f: Frame) -> dict:
    """What an access point says about itself in the Interworking element
    (802.11u) and the Hotspot 2.0 tag. Set by the access point, not checked."""
    out: dict = {}
    for ie_id, data in f.ies:
        if ie_id == IE_INTERWORKING and len(data) in (1, 3, 7, 9):
            out["network_type"] = _ACCESS_NETWORK_TYPES.get(data[0] & 0x0F, f"type {data[0] & 0x0F}")
            out["internet"] = bool(data[0] & 0x10)
            if len(data) in (3, 9) and data[1]:
                group = _VENUE_GROUPS.get(data[1], f"group {data[1]}")
                kind = _VENUE_TYPES.get((data[1], data[2]))
                out["venue"] = f"{group}, {kind}" if kind else group
            if len(data) in (7, 9):
                out["hotspot_id"] = _mac(data[-6:])
        elif ie_id == IE_VENDOR and data[:3] == WFA_OUI and len(data) >= 4 and data[3] == 0x10:
            out["hotspot2"] = True
    return out


def vendor_elements(f: Frame) -> list[str]:
    """Standard elements carried under a vendor OUI (WPA, WMM, WPS, ...)."""
    seen = []
    for ie_id, data in f.ies:
        if ie_id == IE_VENDOR and len(data) >= 4:
            label = _STANDARD_VENDOR_IES.get((bytes(data[:3]), data[3]))
            if label and label not in seen:
                seen.append(label)
    return seen


def french_remote_id(f: Frame) -> Optional[dict]:
    """French Direct Remote ID plate: id, aircraft position, height above
    takeoff, speed, course and the takeoff point. Coordinates are 1e-5 deg."""
    for ie_id, data in f.ies:
        if ie_id != IE_VENDOR or data[:3] != FRENCH_RID_OUI or len(data) < 4 or data[3] != 1:
            continue
        body, i, out = data[4:], 0, {}
        while i + 2 <= len(body):
            t, n = body[i], body[i + 1]
            v = body[i + 2:i + 2 + n]
            if len(v) != n:
                break
            i += 2 + n
            if t == 0x01 and n == 1:
                out["version"] = v[0]
            elif t == 0x02 and n:
                out["french_id"] = _clean(v.rstrip(b"\x00").decode("utf-8", "replace"), 40)
            elif t == 0x03 and n:
                out["serial"] = _clean(v.rstrip(b"\x00").decode("utf-8", "replace"), 40)
            elif t in (0x04, 0x05, 0x08, 0x09) and n == 4:
                key = {0x04: "latitude", 0x05: "longitude", 0x08: "takeoff_latitude", 0x09: "takeoff_longitude"}[t]
                out[key] = round(int.from_bytes(v, "big", signed=True) / 1e5, 5)
            elif t == 0x06 and n == 2:
                out["altitude_m"] = int.from_bytes(v, "big", signed=True)
            elif t == 0x07 and n == 2:
                out["height_above_takeoff_m"] = int.from_bytes(v, "big", signed=True)
            elif t == 0x0A and n == 1:
                out["speed_m_s"] = v[0]
            elif t == 0x0B and n == 2:
                course = int.from_bytes(v, "big")
                if course < 360:
                    out["course_deg"] = course
        for a, b in (("latitude", "longitude"), ("takeoff_latitude", "takeoff_longitude")):
            if out.get(a) == 0 and out.get(b) == 0:
                out.pop(a), out.pop(b)
        return {k: v for k, v in out.items() if v is not None} or None
    return None


class WifiWatch:
    """Turns frames into hits and events. Keeps a little state for the
    attacks that only show up across frames."""

    DEAUTH_WINDOW = 10.0       # seconds
    DEAUTH_PER_SENDER = 30     # frames from one transmitter in the window; access
                               # points kicking clients (band steering, mesh) stay below
    EVENT_COOLDOWN = 900.0     # seconds before the same event fires again
    TWIN_WINDOW = 300.0        # an open and a protected copy within this long

    def __init__(self, trusted: Optional["TrustedNetworks"] = None) -> None:
        self.trusted = trusted
        self._deauth: dict[str, deque[float]] = {}
        self._ssids: dict[str, dict[str, tuple[str, float]]] = {}  # ssid -> bssid -> (security, when)
        self._fired: dict[str, float] = {}
        self.frames = 0
        self.beacons = 0
        self.deauths = 0

    def _fire(self, key: str, now: float, cooldown: Optional[float] = None) -> bool:
        if now - self._fired.get(key, -1e9) < (cooldown or self.EVENT_COOLDOWN):
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
        event = self._twin_event(f, now)
        if event is None and self.trusted is not None:
            event = self.trusted.hear(f, time.time())
            if event is not None and not self._fire("trusted:" + event.key, now, 6 * 3600):
                event = None
        return self._hit(f), event

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

        french = french_remote_id(f)
        if french:
            tags.append("remote-id-fr")
            evidence.append("French Remote ID beacon")
            state.update(french)
            if not rid:
                name = french.get("french_id") or french.get("serial") or name or "Drone"
        if any(i == IE_VENDOR and d[:3] == DJI_DRONEID_OUI for i, d in f.ies):
            tags.append("dji-droneid")
            evidence.append("DJI DroneID beacon")

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
        state.update(interworking_info(f))
        elements = vendor_elements(f)
        if elements:
            state["elements"] = ", ".join(elements)
        state["evidence"] = ", ".join(evidence)
        return Hit(mac=bssid, name=name, tags=[TAG_PREFIX + t for t in tags], rssi=f.rssi,
                   state={k: v for k, v in state.items() if v is not None}, service_data=service_data)


def _is_locally_administered(mac: str) -> bool:
    try:
        return bool(int(mac[:2], 16) & 0x02)
    except ValueError:
        return False


class TrustedNetworks:
    """Watch the Wi-Fi names the operator trusts (their own network, the
    neighbours'). For the first days after a name is added, every access
    point that sends it is learned. After that, a new access point with that
    name warns when it looks unlike the learned ones: weaker security (open
    or WEP where the learned ones use a password), a maker the learned ones
    do not share (or a made-up address), or far louder than any of them.
    A new access point from a learned maker (another mesh node) is learned
    quietly. BlueWatch never joins the network or asks for its password.
    Idea from OffGridPete/Fieldwatch v1.1.35 (Trusted networks)."""

    LOUDER_DB = 15
    MAX_APS = 64
    _SEC_RANK = {"open": 0, "wep": 1, "protected": 2}

    def __init__(self, book: Optional[dict] = None) -> None:
        # ssid -> {"added": epoch, "aps": {bssid: {"sec": str, "rssi": int|None, "seen": epoch}}}
        self.book: dict = book if isinstance(book, dict) else {}
        self.learn_days = 3
        self.dirty = False

    def sync(self, ssids: list[str], learn_days: int, now: float) -> None:
        """Follow the list in settings: add new names (learning starts now),
        forget removed ones."""
        self.learn_days = max(0, int(learn_days))
        wanted = [s for s in dict.fromkeys(x.strip() for x in ssids) if s]
        for ssid in list(self.book):
            if ssid not in wanted:
                del self.book[ssid]
                self.dirty = True
        for ssid in wanted:
            if ssid not in self.book:
                self.book[ssid] = {"added": now, "aps": {}}
                self.dirty = True

    def learning(self, ssid: str, now: float) -> bool:
        net = self.book.get(ssid)
        return bool(net) and now < net["added"] + self.learn_days * 86400

    def status(self, now: float) -> list[dict]:
        return [{"ssid": ssid, "access_points": len(net["aps"]),
                 "learning_hours_left": max(0, round((net["added"] + self.learn_days * 86400 - now) / 3600, 1))}
                for ssid, net in self.book.items()]

    def _learn(self, net: dict, bssid: str, f: Frame, now: float) -> None:
        aps = net["aps"]
        ap = aps.get(bssid)
        if ap is None:
            if len(aps) >= self.MAX_APS:
                return
            ap = aps[bssid] = {"sec": f.security, "rssi": f.rssi, "seen": now}
            self.dirty = True
        else:
            if f.rssi is not None and (ap.get("rssi") is None or f.rssi > ap["rssi"]):
                ap["rssi"] = f.rssi
            if now - ap.get("seen", 0) > 3600:
                ap["seen"] = now
                self.dirty = True

    def hear(self, f: Frame, now: float) -> Optional[Event]:
        if f.subtype not in (SUBTYPE_BEACON, SUBTYPE_PROBE_RESP) or not f.ssid:
            return None
        net = self.book.get(f.ssid)
        if net is None:
            return None
        bssid = f.addr3 if f.subtype == SUBTYPE_BEACON else f.addr2
        if bssid in net["aps"] or self.learning(f.ssid, now):
            self._learn(net, bssid, f, now)
            return None
        known = net["aps"]
        if not known:
            self._learn(net, bssid, f, now)  # nothing learned yet: start with this one
            return None
        reasons = []
        best_sec = max(self._SEC_RANK.get(a.get("sec"), 2) for a in known.values())
        if self._SEC_RANK.get(f.security, 2) < best_sec:
            reasons.append(f"it is {f.security}, the known access points use a password")
        ouis = {b[:8] for b in known}
        if _is_locally_administered(bssid) and not any(_is_locally_administered(b) for b in known):
            reasons.append("its address is made up (locally administered)")
        elif bssid[:8] not in ouis:
            reasons.append(f"its maker block {bssid[:8]} is not one of the known access points'")
        loudest = max((a["rssi"] for a in known.values() if a.get("rssi") is not None), default=None)
        if f.rssi is not None and loudest is not None and f.rssi >= loudest + self.LOUDER_DB:
            reasons.append(f"it is {f.rssi - loudest} dB louder than any known one")
        if not reasons:
            self._learn(net, bssid, f, now)  # same maker, same security: another node
            return None
        return Event("trusted_network", f"{f.ssid}|{bssid}", "⚠ Unknown access point on a trusted network",
                     f"\"{f.ssid}\" is now also sent by {bssid} (channel {f.channel or '?'}"
                     f"{', ' + str(f.rssi) + ' dBm' if f.rssi is not None else ''}), and {'; '.join(reasons)}. "
                     "It could be a new router or a copy set up to catch devices that join by name. "
                     "BlueWatch cannot tell which; check it yourself.")
