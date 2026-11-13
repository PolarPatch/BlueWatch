"""Fieldwatch catalogs 97-111 (v1.1.28-v1.1.44): advertisement decoders,
new signatures, Wi-Fi decoders and trusted networks."""

import struct
import unittest

from bluewatch import advdecode, classifier, wifi
from tests.test_wifi import beacon, frame, ie


def classify(**kwargs):
    return classifier.classify_device(None, **kwargs)


def uuid16(short):
    return f"0000{short}-0000-1000-8000-00805f9b34fb"


def block(blocks, kind):
    return next(b for b in blocks if b["kind"] == kind)


class AdvDecodeTests(unittest.TestCase):
    def test_bthome_reading_and_open_door(self):
        # v2 unencrypted; temperature 23.45 C, humidity 50.55 %, door open
        data = bytes([0x40, 0x02]) + struct.pack("<h", 2345) + bytes([0x03]) + struct.pack("<H", 5055) + bytes([0x1A, 1])
        b = advdecode.decode_bthome(data)
        rows = dict(map(tuple, b["rows"]))
        self.assertEqual(rows["Temperature"], "23.45 °C")
        self.assertEqual(rows["Humidity"], "50.55 %")
        self.assertEqual(rows["Door"], "Open")
        self.assertEqual((b["chip"], b["alert"]), ("Door open", True))
        self.assertEqual(classify(service_uuids=[uuid16("fcd2")]), classifier.TYPE_SMART_HOME)

    def test_bthome_encrypted_is_not_opened(self):
        b = advdecode.decode_bthome(bytes([0x41, 0x02, 0x10, 0x20]))
        self.assertIn(["Payload", "encrypted (not opened)"], b["rows"])
        self.assertNotIn("chip", b)

    def test_bthome_unknown_object_stops(self):
        b = advdecode.decode_bthome(bytes([0x40, 0x01, 77, 0xEE, 0x02, 0x00]))
        self.assertEqual([r[0] for r in b["rows"]], ["Version", "Battery"])

    def test_matter_commissionable(self):
        data = bytes([0x00, 0x34, 0x0F]) + struct.pack("<HH", 0xFFF1, 0x8000) + bytes([0x01])
        b = advdecode.decode_matter(data)
        rows = dict(map(tuple, b["rows"]))
        self.assertEqual(rows["Vendor ID"], "0xFFF1")
        self.assertEqual(rows["Product ID"], "0x8000")
        self.assertEqual(rows["Discriminator"], str(0xF34))
        self.assertEqual(b["chip"], "Matter setup")

    def test_homekit_unpaired_lock(self):
        value = bytes([0x01]) + bytes(6) + struct.pack("<H", 6) + struct.pack("<H", 3) + bytes([2, 2])
        mfg = {0x004C: bytes([0x06, 0x31]) + value}
        blocks = advdecode.decode_adv_state(mfg, None)
        b = block(blocks, "homekit")
        self.assertIn(["Category", "Lock"], b["rows"])
        self.assertEqual(b["chip"], "HomeKit lock unpaired")
        self.assertEqual(advdecode.name_hint(blocks), "HomeKit Lock")

    def test_find_my_forms(self):
        key = advdecode.decode_findmy(bytes([0x04 | 0x80]) + bytes(24))
        self.assertIn(["Battery", "low"], key["rows"])
        short = advdecode.decode_findmy(bytes([0x00, 0x01]))
        self.assertTrue(short["near_owner_hint"])

    def test_find_hub_is_a_tracker_not_a_beacon(self):
        sep = {uuid16("feaa"): bytes([0x41]) + bytes(20)}
        self.assertEqual(classify(service_uuids=[uuid16("feaa")], service_data=sep), classifier.TYPE_TRACKER)
        b = advdecode.decode_find_hub(sep[uuid16("feaa")])
        self.assertTrue(b["separated"])
        eddystone_url = {uuid16("feaa"): bytes([0x10, 0x00, 0x03]) + b"example"}
        self.assertEqual(classify(service_uuids=[uuid16("feaa")], service_data=eddystone_url),
                         classifier.TYPE_SMART_HOME)

    def test_smarttag_separated_keeps_privacy_id(self):
        data = bytes([0x11, 1, 0, 0]) + bytes.fromhex("0102030405060708") + bytes([0x07])
        b = advdecode.decode_smarttag(data)
        self.assertTrue(b["separated"])
        self.assertEqual(b["tag_id"], "smarttag:0102030405060708")
        self.assertIn(["Battery", "full"], b["rows"])
        with_owner = advdecode.decode_smarttag(bytes([0x14]) + bytes(12))
        self.assertIs(with_owner["separated"], False)
        self.assertNotIn("tag_id", with_owner)

    def test_sidewalk_needs_the_ama_uuid(self):
        mfg = {0x0171: bytes([0x04, 0b00010010])}  # registration, battery normal
        self.assertIsNone(advdecode.decode_adv_state(mfg, None, []))
        b = block(advdecode.decode_adv_state(mfg, None, [uuid16("fe03")]), "sidewalk")
        self.assertIn(["Beacon", "registration"], b["rows"])
        self.assertIn(["Battery", "normal"], b["rows"])

    def test_exposure_notification_label(self):
        self.assertIn("Exposure Notification", classifier.get_uuid_names([uuid16("fd6f")]))
        self.assertNotIn("Apple Continuity", classifier.get_uuid_names([uuid16("fd6f")]))
        b = advdecode.decode_exposure(bytes(20))
        self.assertEqual(len(b["rows"]), 2)

    def test_microsoft_computer_name(self):
        payload = bytes([0x01, 0x09, 0x21]) + bytes(7) + b"DESKTOP-ABC"
        b = advdecode.decode_microsoft(payload)
        self.assertIn(["Device", "Windows desktop"], b["rows"])
        self.assertIn(["Computer name", "DESKTOP-ABC"], b["rows"])
        self.assertEqual(b["name"], "DESKTOP-ABC")
        mine_only = advdecode.decode_microsoft(bytes([0x01, 0x09, 0x20]) + bytes(7) + b"DESKTOP-ABC")
        self.assertNotIn("name", mine_only)


class SignatureTests(unittest.TestCase):
    def test_quest_is_not_glasses(self):
        meta = {0x01AB: b"\x00"}
        self.assertEqual(classify(name="Quest 3S", manufacturer_data=meta), classifier.TYPE_GAMING)
        self.assertEqual(classify(name="Meta Quest Pro", manufacturer_data=meta), classifier.TYPE_GAMING)
        self.assertEqual(classify(name="Questionnaire", manufacturer_data=meta), classifier.TYPE_GLASSES)

    def test_two_way_radios(self):
        for name in ("UV-PRO", "VR-N76", "ICOM BT(ID-52)", "KHS-56BT 1234", "SSM-BT20", "PTT-Z"):
            self.assertEqual(classify(name=name), classifier.TYPE_RADIO, name)
        self.assertEqual(classifier.get_type_label(classifier.TYPE_RADIO), "Two-way Radio")

    def test_new_service_uuids(self):
        self.assertEqual(classify(service_uuids=[uuid16("fa25")]), classifier.TYPE_TRACKER)
        self.assertEqual(classify(service_uuids=[uuid16("fff6")]), classifier.TYPE_SMART_HOME)
        self.assertEqual(classify(service_uuids=[uuid16("fe95")]), classifier.TYPE_SMART_HOME)
        self.assertEqual(classify(service_uuids=["f47b5e2d-4a9e-4c5a-9b3f-8e1d2c3a4b5c"]), classifier.TYPE_PHONE)

    def test_remote_id_authentication(self):
        msg = bytes([0x22, 0x10, 0x03, 0x40]) + struct.pack("<I", 100) + bytes(17)
        state = classifier.decode_drone_remote_id({"0000fffa-0000-1000-8000-00805f9b34fb": bytes([0x0D, 1]) + msg})
        self.assertEqual(state["auth_type"], "UAS ID signature")
        self.assertEqual((state["auth_page"], state["auth_last_page"], state["auth_length"]), (0, 3, 0x40))
        self.assertEqual(state["auth_time"], "2019-01-01T00:01:40Z")


def vendor_ie(oui_hex, vtype, body=b""):
    return ie(221, bytes.fromhex(oui_hex) + bytes([vtype]) + body)


class WifiTests(unittest.TestCase):
    def hit(self, packet):
        return wifi.WifiWatch()._hit(frame(packet))

    def test_french_remote_id(self):
        tlv = lambda t, v: bytes([t, len(v)]) + v
        body = (tlv(1, b"\x01") + tlv(2, b"ABC123SERIAL0001")
                + tlv(4, struct.pack(">i", 4886000)) + tlv(5, struct.pack(">i", 235000))
                + tlv(7, struct.pack(">h", 85)) + tlv(10, b"\x07") + tlv(11, struct.pack(">H", 270)))
        h = self.hit(beacon("62:00:00:00:00:01", "drone", vendor_ie("6a5c35", 1, body)))
        self.assertIn("wifi-sig:remote-id-fr", h.tags)
        self.assertEqual((h.state["latitude"], h.state["longitude"]), (48.86, 2.35))
        self.assertEqual(h.state["height_above_takeoff_m"], 85)
        self.assertEqual(h.state["course_deg"], 270)
        self.assertEqual(h.name, "ABC123SERIAL0001")
        self.assertEqual(classify_tags(h.tags), classifier.TYPE_DRONE)

    def test_dji_droneid_and_setup_networks(self):
        h = self.hit(beacon("60:60:1F:00:00:01", "x", vendor_ie("263712", 0x58, b"\x10\x02")))
        self.assertIn("wifi-sig:dji-droneid", h.tags)
        self.assertEqual(classify_tags(self.hit(beacon("02:00:00:00:00:02", "ExpressLRS TX Backpack")).tags),
                         classifier.TYPE_DRONE)
        self.assertEqual(classify_tags(self.hit(beacon("02:00:00:00:00:03", "EZVIZ_Q12345678")).tags),
                         classifier.TYPE_CAMERA)

    def test_interworking_and_elements_on_hits(self):
        inter = ie(107, bytes([0x13, 7, 1]))  # free public, internet; residential, private residence
        h = self.hit(beacon("02:00:00:00:00:04", "EZVIZ_Q1", inter, vendor_ie("0050f2", 2, b"\x00"),
                            vendor_ie("506f9a", 0x10)))
        self.assertEqual(h.state["network_type"], "free public")
        self.assertTrue(h.state["internet"])
        self.assertEqual(h.state["venue"], "Residential, private residence")
        self.assertTrue(h.state["hotspot2"])
        self.assertEqual(h.state["elements"], "WMM, Hotspot 2.0")


def classify_tags(tags):
    return classifier.classify_wifi(tags)


class TrustedNetworkTests(unittest.TestCase):
    def setUp(self):
        self.t = wifi.TrustedNetworks()
        self.t.sync(["Home"], 3, 0)

    def hear(self, bssid, now, rssi=-60, rsn=True):
        return self.t.hear(frame(beacon(bssid, "Home", rsn=rsn, privacy=rsn, rssi=rssi)), now)

    def test_learns_then_warns(self):
        self.assertIsNone(self.hear("A4:2B:B0:00:00:01", 10))
        self.assertTrue(self.t.learning("Home", 10))
        after = 4 * 86400
        self.assertIsNone(self.hear("A4:2B:B0:00:00:01", after))           # known
        self.assertIsNone(self.hear("A4:2B:B0:00:00:09", after))           # same maker: learned quietly
        self.assertIn("A4:2B:B0:00:00:09", self.t.book["Home"]["aps"])
        ev = self.hear("02:13:37:00:00:01", after, rsn=False)              # open, made-up address
        self.assertEqual(ev.kind, "trusted_network")
        self.assertIn("open", ev.message)
        self.assertIn("made up", ev.message)
        ev = self.hear("00:11:22:00:00:01", after, rssi=-30)              # other maker, much louder
        self.assertIn("00:11:22", ev.message)
        self.assertIn("30 dB louder", ev.message)

    def test_removed_name_is_forgotten(self):
        self.hear("A4:2B:B0:00:00:01", 10)
        self.t.sync([], 3, 20)
        self.assertEqual(self.t.book, {})

    def test_watch_rate_limits(self):
        w = wifi.WifiWatch(trusted=self.t)
        self.t.book["Home"]["added"] = -10 * 86400
        self.t.book["Home"]["aps"]["A4:2B:B0:00:00:01"] = {"sec": "protected", "rssi": -60, "seen": 0}
        f = frame(beacon("02:13:37:00:00:01", "Home"))
        events = [w.feed(f, n)[1] for n in (0, 1, 2)]
        self.assertEqual(sum(e is not None for e in events), 1)


if __name__ == "__main__":
    unittest.main()
