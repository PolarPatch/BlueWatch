"""Fixes from the October 2026 code review: time windows in SQL, Wi-Fi
channel hopping, remote ear signal and the tracker flood watch."""

import asyncio
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from bluewatch import db, wifi_sniffer
from bluewatch.notifications import TagFloodWatch


class TimeWindowTests(unittest.IsolatedAsyncioTestCase):
    async def test_day_window_is_a_day(self):
        # Stored times have a T; SQLite's datetime('now') had a space, so
        # anything from the cutoff's date used to count as inside the window.
        with tempfile.TemporaryDirectory() as directory, patch.object(db, "DB_PATH", Path(directory) / "w.db"):
            await db.init_db()
            mac = "AA:BB:CC:00:00:02"
            await db.upsert_device(mac=mac, rssi=-60)
            async with db._connect() as conn:
                await conn.execute("INSERT INTO sightings (mac, timestamp, rssi) VALUES (?, ?, ?)",
                                   (mac, (datetime.now() - timedelta(hours=30)).isoformat(), -70))
                await conn.commit()
            sightings = await db.get_sightings(mac, days=1)
            self.assertEqual([s.rssi for s in sightings], [-60])

    async def test_last_rssi_skips_ear_sightings(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(db, "DB_PATH", Path(directory) / "r.db"):
            await db.init_db()
            mac = "AA:BB:CC:00:00:03"
            await db.upsert_device(mac=mac, rssi=-55)
            await db.upsert_device(mac=mac, rssi=None)  # heard by an ear only
            rows, _ = await db.get_devices_page(page=1, page_size=10, exclude_randomized=False, show_all=True)
            self.assertEqual([d.last_rssi for d in rows if d.mac == mac], [-55])


class HopTests(unittest.IsolatedAsyncioTestCase):
    async def test_untunable_duplicate_channels_fail_instead_of_spinning(self):
        async def refuse(*cmd):
            return 1, "Invalid argument"
        with patch.object(wifi_sniffer, "_run", refuse):
            with self.assertRaises(RuntimeError):
                await asyncio.wait_for(wifi_sniffer._hop("wlan9", [6, 6]), timeout=2)


class TagFloodTests(unittest.TestCase):
    def test_one_shots_still_counted_in_order(self):
        watch = TagFloodWatch()
        t0 = datetime(2026, 10, 21, 12, 0)
        for i in range(15):
            watch.seen(f"F0:00:00:00:00:{i:02X}", True, t0 + timedelta(seconds=i))
        # A real tag heard over and over keeps the stale ones moving out.
        started = [watch.seen("AA:00:00:00:00:01", False, t0 + timedelta(seconds=80 + i)) for i in range(5)]
        self.assertIn(True, started)
        self.assertEqual(len(watch._sightings), 1)


if __name__ == "__main__":
    unittest.main()
