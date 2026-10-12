import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bluewatch import db, wifi, wifi_sniffer
from bluewatch.classifier import TYPE_ATTACK, TYPE_CAMERA, TYPE_DRONE, classify_device


def mac(text):
    return bytes.fromhex(text.replace(":", ""))


def ie(ie_id, data):
    return bytes([ie_id, len(data)]) + data


def radiotap(rssi=-50, freq=2437):
    # present: flags(1), channel(3), antenna signal(5)
    body = bytes([0]) + b"\x00" + struct.pack("<HH", freq, 0x00a0) + struct.pack("<b", rssi)
    return struct.pack("<BBHI", 0, 0, 8 + len(body), (1 << 1) | (1 << 3) | (1 << 5)) + body


def beacon(bssid, ssid, *extra, privacy=False, rsn=False, rssi=-50):
    hdr = bytes([0x80, 0]) + b"\x00\x00" + b"\xff" * 6 + mac(bssid) + mac(bssid) + b"\x00\x00"
    fixed = b"\x00" * 8 + struct.pack("<HH", 100, 0x0011 if privacy else 0x0001)
    ies = ie(0, ssid.encode()) + ie(3, b"\x06") + (ie(48, b"\x01\x00") if rsn else b"") + b"".join(extra)
    return radiotap(rssi) + hdr + fixed + ies


def deauth(src, dst="FF:FF:FF:FF:FF:FF"):
    return radiotap() + bytes([0xC0, 0]) + b"\x00\x00" + mac(dst) + mac(src) + mac(src) + b"\x00\x00" + b"\x07\x00"


def frame(packet):
    rssi, freq, body = wifi.parse_radiotap(packet)
    return wifi.parse_frame(body, rssi, freq)


class ParseTests(unittest.TestCase):
    def test_beacon(self):
        f = frame(beacon("B4:1E:52:00:00:01", "Home", rsn=True, rssi=-61))
        self.assertEqual((f.ssid, f.channel, f.security, f.rssi), ("Home", 6, "protected", -61))
        self.assertEqual(frame(beacon("AA:00:00:00:00:01", "Cafe")).security, "open")
        self.assertEqual(frame(beacon("AA:00:00:00:00:01", "Old", privacy=True)).security, "wep")

    def test_truncated_input_is_ignored(self):
        packet = beacon("AA:00:00:00:00:01", "x")
        for cut in (3, 10, 20, 40):
            parsed = wifi.parse_radiotap(packet[:cut])
            if parsed:
                self.assertIsNone(wifi.parse_frame(parsed[2]))


class RecognitionTests(unittest.TestCase):
    def hit(self, packet):
        return wifi.WifiWatch().feed(frame(packet), 0.0)[0]

    def test_ordinary_network_is_not_stored(self):
        self.assertIsNone(self.hit(beacon("AA:00:00:00:00:01", "Telenor-1234", rsn=True)))

    def test_axon_and_flock(self):
        h = self.hit(beacon("AA:00:00:00:00:02", "AB3-X1234"))
        self.assertEqual(h.tags, ["wifi-sig:axon-ssid"])
        self.assertEqual(classify_device(None, h.name, h.tags), TYPE_CAMERA)
        self.assertIn("wifi-sig:flock-oui", self.hit(beacon("B4:1E:52:00:00:03", "anything")).tags)
        self.assertIsNotNone(self.hit(beacon("AA:00:00:00:00:04", "Flock")))
        self.assertIsNone(self.hit(beacon("AA:00:00:00:00:04", "Flockton Road")))

    def test_attack_tools(self):
        h = self.hit(beacon("02:C0:CA:00:00:05", "Pineapple_ABCD"))
        self.assertEqual(classify_device(None, h.name, h.tags), TYPE_ATTACK)
        self.assertIn("Hak5", h.state["evidence"])
        payload = json.dumps({"name": "sniffy", "pwnd_tot": 42, "version": "1.5.5"}).encode()
        chunks = [ie(222, payload[i:i + 255]) for i in range(0, len(payload), 255)]
        h = self.hit(beacon("DE:AD:BE:EF:DE:AD", "", *chunks))
        self.assertEqual((h.name, h.state["handshakes"]), ("sniffy", 42))
        self.assertEqual(classify_device(None, h.name, h.tags), TYPE_ATTACK)

    def test_remote_id_beacon(self):
        basic = bytes([0x02, 0x12]) + b"1581F4XYZ".ljust(20, b"\x00") + b"\x00" * 3
        loc = bytes([0x12, 0x20, 0, 0, 0]) + struct.pack("<ii", 599000000, 107000000) + b"\x00" * 2 \
            + struct.pack("<HH", 2400, 2100) + b"\x00" * 6
        pack = bytes([0xF2, 25, 2]) + basic + loc
        h = self.hit(beacon("60:60:1F:00:00:06", "DRONE", ie(221, bytes.fromhex("fa0bbc0d") + b"\x07" + pack)))
        self.assertEqual(h.name, "1581F4XYZ")
        self.assertEqual(classify_device(None, h.name, h.tags, service_data=h.service_data), TYPE_DRONE)
        from bluewatch.classifier import decode_drone_remote_id
        state = decode_drone_remote_id(h.service_data)
        self.assertAlmostEqual(state["latitude"], 59.9)


class EventTests(unittest.TestCase):
    def test_deauth_flood_fires_once(self):
        watch = wifi.WifiWatch()
        events = [watch.feed(frame(deauth("AA:BB:CC:00:00:01")), t * 0.2)[1] for t in range(40)]
        self.assertEqual(sum(e is not None for e in events), 1)
        self.assertEqual([e.kind for e in events if e], ["deauth_flood"])

    def test_a_few_deauths_are_normal(self):
        watch = wifi.WifiWatch()
        self.assertTrue(all(watch.feed(frame(deauth("AA:BB:CC:00:00:01")), t * 5.0)[1] is None for t in range(30)))

    def test_evil_twin(self):
        watch = wifi.WifiWatch()
        self.assertIsNone(watch.feed(frame(beacon("AA:00:00:00:00:10", "Office", rsn=True)), 0)[1])
        self.assertIsNone(watch.feed(frame(beacon("AA:00:00:00:00:11", "Office", rsn=True)), 1)[1])
        event = watch.feed(frame(beacon("02:00:00:00:00:12", "Office")), 2)[1]
        self.assertEqual(event.kind, "evil_twin")
        self.assertIsNone(watch.feed(frame(beacon("02:00:00:00:00:12", "Office")), 3)[1])


class PcapAndStorageTests(unittest.IsolatedAsyncioTestCase):
    async def test_pcap_replay_and_store(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cap.pcap"
            packets = [beacon("AA:00:00:00:00:20", "Home", rsn=True), beacon("AA:00:00:00:00:21", "pwned")]
            with open(path, "wb") as fh:
                fh.write(struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 127))
                for n, p in enumerate(packets):
                    fh.write(struct.pack("<IIII", 1000 + n, 0, len(p), len(p)) + p)
            frames = [f async for _, f in wifi_sniffer.frames_from_pcap(str(path))]
            self.assertEqual([f.ssid for f in frames], ["Home", "pwned"])

            hit = wifi.WifiWatch().feed(frames[1], 0)[0]
            with patch.object(db, "DB_PATH", Path(directory) / "w.db"):
                await db.init_db()
                device, is_new = await db.upsert_device(
                    mac=hit.mac, friendly_name=hit.name, rssi=hit.rssi, service_uuids=hit.tags,
                    bt_type="wifi", rf_state=hit.state)
                self.assertTrue(is_new)
                self.assertEqual(device.bt_type, "wifi")
                self.assertEqual(db._computed_device_type(device), TYPE_ATTACK)
                self.assertEqual(device.rf_state["evidence"], "ESP deauther SSID")


if __name__ == "__main__":
    unittest.main()
