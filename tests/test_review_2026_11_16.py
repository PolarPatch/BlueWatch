"""SquachWatch-CYD v1.45, Fieldwatch catalogs 112-113, blesploit
device-library and AntiHunter's Wi-Fi attack ideas (review 2026-11-16)."""

import struct
import unittest

from bluewatch import classifier as c
from bluewatch import wifi


def u16(x):
    return f"0000{x}-0000-1000-8000-00805f9b34fb"


def classify(**kw):
    return c.classify_device(kw.pop("vendor", None), **kw)


class ClassifierTest(unittest.TestCase):
    def test_busy_bar_is_not_a_flipper_zero(self):
        self.assertEqual(classify(manufacturer_data={0x0E29: b"\x01"}), c.TYPE_SMART_HOME)
        self.assertEqual(classify(service_uuids=[u16("308a")], mac="0C:FA:22:00:41:54"), c.TYPE_SMART_HOME)
        # A real Zero: its UUID, even from Flipper's address block
        self.assertEqual(classify(service_uuids=[u16("3082")], mac="80:E1:26:11:22:33"), c.TYPE_FLIPPER)
        self.assertEqual(classify(service_uuids=[u16("3081")], manufacturer_data={0x0E29: b""}), c.TYPE_FLIPPER)

    def test_axon_bwc_tag_and_bodyworn(self):
        ev = c.surveillance_evidence("5A:11:22:33:44:55", None, {0x0059: b"\x00BWCDEVICE\x01"})
        self.assertEqual(ev["vendor"], "Axon")
        self.assertEqual(ev["level"], c.SURVEILLANCE_HIGH)
        ev = c.surveillance_evidence("5A:11:22:33:44:55", None, None, None, {u16("fe6c"): b"ECIVEDCWB"})
        self.assertEqual(ev["level"], c.SURVEILLANCE_HIGH)
        self.assertEqual(classify(manufacturer_data={0x0059: b"BWCDEVICE"}, mac="5A:11:22:33:44:55"), c.TYPE_CAMERA)
        ev = c.surveillance_evidence(None, "BodyWorn Remote")
        self.assertEqual(ev["vendor"], "BodyWorn (Utility)")
        self.assertEqual(classify(name="BodyWorn Remote"), c.TYPE_CAMERA)

    def test_tracker_and_glasses_uuids_also_as_service_data(self):
        self.assertEqual(classify(service_data={u16("fd84"): b"\x01\x02"}), c.TYPE_TRACKER)
        self.assertEqual(classify(service_uuids=[u16("fe65")]), c.TYPE_TRACKER)
        self.assertEqual(classify(service_uuids=[u16("fe45")]), c.TYPE_GLASSES)

    def test_two_way_radios(self):
        for name in ("ICOM BT(IC-705)", "ICOM BT(ID-5200)", "ICOM BT-003", "TD-H9 Pro", "ASB99C2F0", "walkie-talkie"):
            self.assertEqual(classify(name=name), c.TYPE_RADIO, name)
        self.assertNotEqual(classify(name="ASB99C2F0X"), c.TYPE_RADIO)
        self.assertEqual(classify(service_uuids=["00000001-ba2a-46c9-ae49-01b0961f68bb"]), c.TYPE_RADIO)
        self.assertEqual(classify(service_uuids=["2320ae58-8394-4652-95f7-0a872ac0958f"]), c.TYPE_RADIO)

    def test_catalog_names(self):
        cases = {
            "70mai_M500_80da": c.TYPE_VEHICLE, "BlackVue DR900X": c.TYPE_VEHICLE, "OBDII": c.TYPE_VEHICLE,
            "Galaxy Watch6 (A1B2)": c.TYPE_WATCH, "soundcore Liberty 4": c.TYPE_HEADPHONES,
            "WHOOP 4C1234": c.TYPE_WEARABLE, "[TV] Samsung 7 Series": c.TYPE_TV, "[AV] Samsung Soundbar": c.TYPE_SPEAKER,
            "ET-2850 Series": c.TYPE_PRINTER, "U6-Lite": c.TYPE_NETWORK, "LYWSD03MMC": c.TYPE_SMART_HOME,
            "LAP-C301S-WJP": c.TYPE_SMART_HOME,
        }
        for name, want in cases.items():
            self.assertEqual(classify(name=name), want, name)

    def test_catalog_uuids_and_company_ids(self):
        self.assertEqual(classify(service_uuids=[u16("fea0")]), c.TYPE_TV)
        self.assertEqual(classify(service_uuids=[u16("fe79")]), c.TYPE_PRINTER)
        self.assertEqual(classify(service_uuids=["c5163c4b-9b63-570d-a3a8-407716f04276"]), c.TYPE_WEARABLE)
        self.assertEqual(classify(service_data={u16("a201"): b"\x00"}), c.TYPE_SMART_HOME)
        self.assertEqual(classify(service_uuids=["2141e110-213a-11e6-b67b-9e71128cae77"]), c.TYPE_SMART_HOME)
        self.assertEqual(classify(manufacturer_data={0x06A8: b"\x00"}), c.TYPE_SMART_HOME)
        self.assertEqual(classify(manufacturer_data={0x0909: b"\x00"}), c.TYPE_VEHICLE)

    def test_tesla_name_needs_hex(self):
        self.assertEqual(classify(name="S0123456789abcdef0", service_uuids=[u16("1122")]), c.TYPE_VEHICLE)
        self.assertNotEqual(classify(name="Samsung Galaxy A5x", service_uuids=[u16("1122")]), c.TYPE_VEHICLE)

    def test_apple_nearby_info_is_a_phone_guess(self):
        nearby = bytes([0x10, 0x05, 0x01, 0x18, 0x00, 0x00, 0x00])
        self.assertEqual(classify(manufacturer_data={0x004C: nearby}, mac="6A:11:22:33:44:55"), c.TYPE_PHONE)
        self.assertEqual(classify(service_uuids=[u16("fef3")]), c.TYPE_PHONE)

    def test_wifi_tags(self):
        self.assertEqual(c.classify_wifi(["wifi-sig:drone-oui"]), c.TYPE_DRONE)
        self.assertEqual(c.classify_wifi(["wifi-sig:camera-oui", "wifi-sig:deauther"]), c.TYPE_ATTACK)


def beacon(bssid: str, ssid: str, subtype=wifi.SUBTYPE_BEACON, addr1="FF:FF:FF:FF:FF:FF") -> wifi.Frame:
    return wifi.Frame(subtype=subtype, addr1=addr1, addr2=bssid, addr3=bssid, channel=6, ssid=ssid,
                      security="protected", ies=[(0, ssid.encode())])


def eapol_bytes(ap: bytes, client: bytes, msg: int, pmkid=False) -> bytes:
    fc = bytes([0x88, 0x02 if msg in (1, 3) else 0x01])      # QoS data, FromDS / ToDS
    if msg in (1, 3):
        addrs = client + ap + ap
    else:
        addrs = ap + client + ap
    hdr = fc + b"\x00\x00" + addrs + b"\x00\x00" + b"\x00\x00"   # seq + QoS
    info = {1: 0x008A, 2: 0x010A, 3: 0x13CA, 4: 0x030A}[msg]
    key_data = b"\xdd\x14\x00\x0f\xac\x04" + b"\x11" * 16 if pmkid else b""
    body = bytes([2, 3]) + struct.pack(">H", 95 + len(key_data)) + bytes([2]) + struct.pack(">H", info)
    body += b"\x00" * (97 - len(body)) + struct.pack(">H", len(key_data)) + key_data
    return hdr + b"\xaa\xaa\x03\x00\x00\x00\x88\x8e" + body


class WifiTest(unittest.TestCase):
    def test_new_oui_tags(self):
        w = wifi.WifiWatch()
        hit, _ = w.feed(beacon("38:1D:14:00:00:01", "Skydio-X10"), 0)
        self.assertIn("wifi-sig:drone-oui", hit.tags)
        hit, _ = w.feed(beacon("02:00:00:00:00:09", "IC-705"), 0)
        self.assertIn("wifi-sig:radio-ssid", hit.tags)
        hit, _ = w.feed(beacon("02:00:00:00:00:0A", "osmo_pocket3"), 0)
        self.assertIn("wifi-sig:osmo-ssid", hit.tags)

    def test_deauth_to_broadcast_needs_fewer_frames(self):
        w = wifi.WifiWatch()
        f = wifi.Frame(subtype=wifi.SUBTYPE_DEAUTH, addr1="FF:FF:FF:FF:FF:FF", addr2="AA:BB:CC:00:00:01", addr3="AA:BB:CC:00:00:01")
        events = [w.feed(f, i * 0.1)[1] for i in range(6)]
        self.assertEqual(events[-1].kind, "deauth_flood")
        w = wifi.WifiWatch()
        f.addr1 = "11:22:33:44:55:66"
        self.assertTrue(all(w.feed(f, i * 0.1)[1] is None for i in range(10)))

    def test_beacon_flood_after_warmup(self):
        w = wifi.WifiWatch()
        # warm-up: 100 real networks at once, no alert
        for i in range(100):
            _, ev = w.feed(beacon(f"10:00:00:00:00:{i:02X}", f"Net{i}"), 1 + i * 0.01)
            self.assertIsNone(ev)
        events = []
        for i in range(60):
            _, ev = w.feed(beacon(f"12:34:56:00:{i // 256:02X}:{i % 256:02X}", f"FREE WIFI {i}"), 300 + i * 0.1)
            events.append(ev)
        kinds = [e.kind for e in events if e]
        self.assertEqual(kinds, ["beacon_flood"])

    def test_karma(self):
        w = wifi.WifiWatch()
        evs = [w.feed(beacon("00:13:37:00:00:01", ssid, wifi.SUBTYPE_PROBE_RESP, "AA:00:00:00:00:01"), i)[1]
               for i, ssid in enumerate(["Home", "Starbucks", "Airport WiFi", "eduroam", "Hotel"])]
        self.assertEqual(evs[-1].kind, "karma")
        w = wifi.WifiWatch()
        self.assertTrue(all(w.feed(beacon("00:11:22:00:00:01", "Home", wifi.SUBTYPE_PROBE_RESP), i)[1] is None
                            for i in range(10)))

    def test_eapol_parse(self):
        ap, client = bytes.fromhex("001122334455"), bytes.fromhex("021111111111")
        f = wifi.parse_frame(eapol_bytes(ap, client, 1, pmkid=True))
        self.assertEqual((f.subtype, f.eapol_msg, f.pmkid), (wifi.SUBTYPE_EAPOL, 1, True))
        self.assertEqual((f.addr2, f.addr1), ("00:11:22:33:44:55", "02:11:11:11:11:11"))
        self.assertEqual(wifi.parse_frame(eapol_bytes(ap, client, 2)).eapol_msg, 2)
        self.assertEqual(wifi.parse_frame(eapol_bytes(ap, client, 3)).eapol_msg, 3)
        self.assertEqual(wifi.parse_frame(eapol_bytes(ap, client, 4)).eapol_msg, 4)
        self.assertIsNone(wifi.parse_frame(b"\x88\x42" + b"\x00" * 60))  # protected data

    def test_pmkid_harvest_across_access_points(self):
        w = wifi.WifiWatch()
        client = bytes.fromhex("02aabbccddee")
        events = []
        for i in range(6):
            f = wifi.parse_frame(eapol_bytes(bytes([0, 0x11, 0x22, 0, 0, i]), client, 1, pmkid=True))
            events.append(w.feed(f, i)[1])
        self.assertEqual([e.kind for e in events if e], ["eapol_harvest"])

    def test_normal_handshake_is_quiet(self):
        w = wifi.WifiWatch()
        ap, client = bytes.fromhex("001122334455"), bytes.fromhex("021111111111")
        for i in range(5):  # a phone rejoining five times, answering each time
            for msg in (1, 2, 3, 4):
                _, ev = w.feed(wifi.parse_frame(eapol_bytes(ap, client, msg)), i * 10 + msg * 0.01)
                self.assertIsNone(ev)

    def test_unanswered_message_one(self):
        w = wifi.WifiWatch()
        ap, client = bytes.fromhex("001122334455"), bytes.fromhex("021111111111")
        evs = [w.feed(wifi.parse_frame(eapol_bytes(ap, client, 1, pmkid=True)), i * 5)[1] for i in range(4)]
        self.assertEqual(evs[-1].kind, "eapol_harvest")


if __name__ == "__main__":
    unittest.main()
