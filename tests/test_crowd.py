import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from aiohttp.test_utils import TestClient, TestServer

from bluewatch import crowd, db


class EstimateTests(unittest.TestCase):
    def test_rotation_counts_once(self):
        rows = [("A", 0, -60, "phone"), ("A", 100, -62, "phone"),
                ("B", 160, -61, "phone"), ("B", 290, -60, "phone")]   # A rotated into B
        self.assertEqual(crowd.estimate(rows)["people"], 1)

    def test_overlapping_or_different_loudness_are_two(self):
        overlap = [("A", 0, -60, "phone"), ("A", 200, -60, "phone"), ("B", 100, -60, "phone")]
        self.assertEqual(crowd.estimate(overlap)["people"], 2)
        apart = [("A", 0, -55, "phone"), ("B", 200, -75, "phone")]
        self.assertEqual(crowd.estimate(apart)["people"], 2)

    def test_what_counts(self):
        rows = [("P", 0, -60, "phone"), ("W", 0, -60, "watch"), ("E", 0, -65, "audio"),
                ("T", 0, -50, "tracker"), ("U", 0, -50, "unknown"), ("TV", 0, -40, "tv"),
                ("FAR", 0, -90, "phone")]
        self.assertEqual(crowd.estimate(rows), {"people": 1, "devices": 3, "addresses": 3})


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_api(self):
        from bluewatch.webapp.server import WebServer
        with tempfile.TemporaryDirectory() as directory, patch.object(db, "DB_PATH", Path(directory) / "c.db"):
            await db.init_db()
            now = datetime.now()
            for days in range(1, 4):
                b = (now - timedelta(days=days)).replace(minute=now.minute - now.minute % 5, second=0, microsecond=0)
                await db.save_crowd_bucket(5, b, {"people": 4 + days, "devices": 9, "addresses": 9})
                m = (now - timedelta(days=days)).replace(second=0, microsecond=0)
                await db.save_crowd_bucket(1, m, {"people": 1, "devices": 1, "addresses": 1})
            await db.upsert_device(mac="7A:00:00:00:00:01", friendly_name="iPhone", rssi=-60)
            async with TestClient(TestServer(WebServer().app)) as client:
                r = await client.get("/api/crowd?range=7d")
                data = await r.json()
                self.assertEqual(data["usual_now"], 6)
                self.assertEqual(len(data["series"]), 3)
                self.assertIn("people", data["now"])
                r = await client.get("/api/crowd?range=7d&minutes=1")
                data = await r.json()
                self.assertEqual((data["usual_now"], data["bucket_minutes"]), (1, 1))
                r = await client.get("/api/crowd?minutes=7")
                self.assertEqual((await r.json())["bucket_minutes"], 5)
                r = await client.get("/crowd")
                self.assertIn("People now", await r.text())


if __name__ == "__main__":
    unittest.main()
