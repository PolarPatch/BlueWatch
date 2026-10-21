"""Timestamps leave BlueWatch as UTC with Z, read in the zone they were
written in (#10)."""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from aiohttp.test_utils import TestClient, TestServer

from bluewatch import config, db, timefmt


class Zone:
    """Run with BLUEWATCH_TIMEZONE set to name."""

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.patch = patch.object(config, "TIMEZONE", self.name)
        self.patch.start()
        timefmt._zone = timefmt._UNSET

    def __exit__(self, *exc):
        self.patch.stop()
        timefmt._zone = timefmt._UNSET


class TimefmtTests(unittest.TestCase):
    def test_legacy_local_value(self):
        # The issue's example: written at 12:00 on a UTC+10 server.
        with Zone("Australia/Brisbane"):
            self.assertEqual(timefmt.to_iso("2026-10-13T12:00:00"), "2026-10-13T02:00:00Z")
            self.assertEqual(timefmt.to_iso("2026-10-13 12:00:05.250000"), "2026-10-13T02:00:05.250000Z")
            self.assertEqual(timefmt.to_iso(datetime(2026, 10, 13, 12, 0)), "2026-10-13T02:00:00Z")

    def test_daylight_saving(self):
        # Oslo is UTC+2 in summer and UTC+1 in winter; each value keeps its own.
        with Zone("Europe/Oslo"):
            self.assertEqual(timefmt.to_iso("2026-07-01T12:00:00"), "2026-07-01T10:00:00Z")
            self.assertEqual(timefmt.to_iso("2026-12-01T12:00:00"), "2026-12-01T11:00:00Z")

    def test_aware_and_other_values_untouched(self):
        with Zone("Europe/Oslo"):
            for value in ("2026-10-13T02:00:00Z", "2026-10-13T12:00:00+10:00", "2026-10-13",
                          "08:15", "Pixel 8", None, 42, -61.5):
                self.assertEqual(timefmt.to_iso(value), value)

    def test_utc_naive_not_shifted(self):
        with Zone("Australia/Brisbane"):
            self.assertEqual(timefmt.utc_naive("2026-10-13 02:00:00"), "2026-10-13T02:00:00Z")

    def test_invalid_zone_falls_back_to_system(self):
        with Zone("Mars/Olympus_Mons"), self.assertLogs("bluewatch.timefmt", "WARNING"):
            expected = datetime(2026, 10, 13, 12, 0).astimezone().astimezone(timezone.utc)
            self.assertEqual(timefmt.to_iso("2026-10-13T12:00:00"), expected.isoformat().replace("+00:00", "Z"))

    def test_from_client(self):
        with Zone("Australia/Brisbane"):
            self.assertEqual(timefmt.from_client("2026-10-13T02:00:00.000Z"), datetime(2026, 10, 13, 12, 0))
            self.assertEqual(timefmt.from_client("2026-10-13T13:00:00+11:00"), datetime(2026, 10, 13, 12, 0))
            self.assertEqual(timefmt.from_client("2026-10-13T12:00"), datetime(2026, 10, 13, 12, 0))
            with self.assertRaises(ValueError):
                timefmt.from_client("yesterday")

    def test_stamp_keeps_keys(self):
        with Zone("Australia/Brisbane"):
            out = timefmt.stamp({"usual": {"08:15": 3}, "rows": [{"at": "2026-10-13T12:00:00"}]})
            self.assertEqual(out, {"usual": {"08:15": 3}, "rows": [{"at": "2026-10-13T02:00:00Z"}]})


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_device_list_sends_utc(self):
        from bluewatch.webapp.server import WebServer
        with tempfile.TemporaryDirectory() as directory, patch.object(db, "DB_PATH", Path(directory) / "t.db"), \
                Zone(None):
            await db.init_db()
            await db.upsert_device(mac="AA:BB:CC:00:00:01", friendly_name="Pixel", rssi=-60)
            async with TestClient(TestServer(WebServer().app)) as client:
                data = await (await client.get("/api/device/AA:BB:CC:00:00:01")).json()
                seen = data["device"]["last_seen"]
                self.assertTrue(seen.endswith("Z"), seen)
                # A device seen just now is just now, whatever the zones.
                age = datetime.now(timezone.utc) - datetime.fromisoformat(seen.replace("Z", "+00:00"))
                self.assertLess(abs(age.total_seconds()), 60)


if __name__ == "__main__":
    unittest.main()
