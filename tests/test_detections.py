import unittest
from datetime import datetime, timedelta

from bluewatch.classifier import (
    FLOCK_GATT_SERVICE_UUID, SURVEILLANCE_HIGH, SURVEILLANCE_LOW, SURVEILLANCE_MEDIUM,
    TYPE_CAMERA, classify_device, surveillance_evidence,
)
from bluewatch.notifications import TagFloodWatch


def level(**kwargs):
    found = surveillance_evidence(kwargs.get("mac"), kwargs.get("name"), kwargs.get("mfg"),
                                  kwargs.get("uuids"), kwargs.get("sdata"))
    return found and found["level"]


class SurveillanceTests(unittest.TestCase):
    def test_axon_ids(self):
        self.assertEqual(level(mfg={0x034D: b"\x01"}), SURVEILLANCE_MEDIUM)
        self.assertEqual(level(mfg={0x034D: b"\x01"}, uuids=["fc81"]), SURVEILLANCE_HIGH)

    def test_flock_gatt_service(self):
        self.assertEqual(level(uuids=[FLOCK_GATT_SERVICE_UUID]), SURVEILLANCE_MEDIUM)
        self.assertEqual(level(name="Flock-1A2B", uuids=[FLOCK_GATT_SERVICE_UUID.upper()]), SURVEILLANCE_HIGH)
        self.assertEqual(classify_device(None, None, [FLOCK_GATT_SERVICE_UUID]), TYPE_CAMERA)

    def test_raven_range(self):
        self.assertEqual(level(uuids=["3101"]), SURVEILLANCE_LOW)
        self.assertEqual(level(uuids=["00003101-0000-1000-8000-00805f9b34fb", "3102"]), SURVEILLANCE_MEDIUM)
        self.assertIsNone(level(uuids=["3501", "30ff"]))

    def test_serial_name(self):
        self.assertEqual(level(name="0123456789"), SURVEILLANCE_LOW)
        self.assertEqual(level(name="0123456789", mfg={0x09C8: b"\x01"}), SURVEILLANCE_HIGH)
        self.assertIsNone(level(name="01234567890"))
        self.assertNotEqual(classify_device(None, "0123456789"), TYPE_CAMERA)


class TagFloodTests(unittest.TestCase):
    def setUp(self):
        self.t0 = datetime(2026, 10, 12, 12, 0, 0)

    def test_real_tags_do_not_trip(self):
        watch = TagFloodWatch()
        for tick in range(120):  # 20 minutes of ten tags heard every pass
            now = self.t0 + timedelta(seconds=10 * tick)
            for i in range(10):
                self.assertFalse(watch.seen(f"AA:00:00:00:00:{i:02X}", tick == 0, now))

    def test_one_shot_addresses_trip_once(self):
        watch = TagFloodWatch()
        trips = 0
        for i in range(60):  # a fresh address every 10 s, each heard once
            trips += watch.seen(f"F0:00:00:00:00:{i:02X}", True, self.t0 + timedelta(seconds=10 * i))
        self.assertEqual(trips, 1)
        self.assertTrue(watch.active)

    def test_fast_burst_trips_and_quiets(self):
        watch = TagFloodWatch()
        trips = sum(watch.seen(f"F1:00:00:00:{i // 256:02X}:{i % 256:02X}", True,
                               self.t0 + timedelta(seconds=i)) for i in range(45))
        self.assertEqual(trips, 1)
        later = self.t0 + timedelta(minutes=12)
        watch.seen("AA:00:00:00:00:01", False, later)
        self.assertFalse(watch.active)


if __name__ == "__main__":
    unittest.main()
