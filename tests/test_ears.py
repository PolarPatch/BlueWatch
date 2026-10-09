import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from aiohttp.test_utils import TestClient, TestServer

from bluewatch import db, ears


def item(**overrides):
    base = {"mac": "c0:de:00:00:00:01", "rssi": -60, "at": 1000.0, "by": "Kitchen"}
    base.update(overrides)
    return base


class ParseTests(unittest.TestCase):
    def test_valid_item_is_normalised(self):
        h = ears.parse_heard(item(name="Fridge\x00", m={"76": "0215AB"}, u=["180F", "0x2a19"],
                                  s={"fe2c": "0a0b"}), sent=1002.0)
        self.assertEqual(h.mac, "C0:DE:00:00:00:01")
        self.assertEqual(h.name, "Fridge")
        self.assertEqual(h.age, 2.0)
        self.assertEqual(h.manufacturer_data, {76: bytes.fromhex("0215ab")})
        self.assertEqual(h.service_uuids, ["0000180f-0000-1000-8000-00805f9b34fb",
                                           "00002a19-0000-1000-8000-00805f9b34fb"])
        self.assertIn("0000fe2c-0000-1000-8000-00805f9b34fb", h.service_data)

    def test_bad_items_are_skipped_not_fatal(self):
        bad = [
            item(mac="not-a-mac"),
            item(rssi=True),
            item(rssi=-200),
            item(at=1000.0 - 500),        # far too old
            item(at=1000.0 + 60),         # from the future
            item(m={"76": "zz"}),         # bad hex is dropped, item kept
            "nope",
        ]
        heard, skipped, error = ears.parse_batch({"v": 1, "sent": 1000.0, "heard": bad})
        self.assertIsNone(error)
        self.assertEqual(len(heard), 1)
        self.assertEqual(heard[0].manufacturer_data, {})
        self.assertEqual(skipped, 6)

    def test_batch_level_errors(self):
        self.assertIsNotNone(ears.parse_batch({"v": 2, "sent": 1, "heard": []})[2])
        self.assertIsNotNone(ears.parse_batch({"v": 1, "heard": []})[2])
        too_many = [item()] * (ears.MAX_HEARD_PER_BATCH + 1)
        self.assertIsNotNone(ears.parse_batch({"v": 1, "sent": 1000.0, "heard": too_many})[2])

    def test_bearer_token(self):
        self.assertIsNone(ears.bearer_token(None))
        self.assertIsNone(ears.bearer_token("Bearer something-else"))
        self.assertEqual(ears.bearer_token("Bearer bwear_abc"), "bwear_abc")


class HubTests(unittest.TestCase):
    def test_merges_listeners_and_picks_strongest(self):
        hub = ears.EarHub()
        heard, _, _ = ears.parse_batch({"v": 1, "sent": 1000.0, "heard": [
            item(rssi=-80, by="Kitchen", u=["180f"]),
            item(rssi=-55, by="Garage", name="Car tag"),
        ]})
        hub.take(1, heard)
        live = hub.live_for("c0:de:00:00:00:01")
        self.assertEqual([r["listener"] for r in live], ["Garage", "Kitchen"])
        devices, rows = hub.drain()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].rssi, -55)
        self.assertEqual(devices[0].name, "Car tag")
        self.assertEqual(len(devices[0].service_uuids), 1)
        self.assertEqual(len(rows), 2)
        # Drained means drained: nothing is replayed on the next pass.
        self.assertEqual(hub.drain(), ([], []))
        self.assertTrue(hub.ear_status(1)["online"])


class EndToEndTests(unittest.IsolatedAsyncioTestCase):
    async def test_ear_lifecycle(self):
        from bluewatch.webapp.server import WebServer

        with tempfile.TemporaryDirectory() as directory, \
                patch.object(db, "DB_PATH", Path(directory) / "ears.db"), \
                patch.object(ears, "HUB", ears.EarHub()):
            await db.init_db()
            server = WebServer()
            async with TestClient(TestServer(server.app)) as client:
                r = await client.get("/api/ears/v1/hello")
                self.assertEqual(r.status, 401)

                r = await client.post("/api/ears", json={"name": "Home Assistant"})
                created = await r.json()
                token = created["token"]
                auth = {"Authorization": "Bearer " + token}

                r = await client.get("/api/ears/v1/hello", headers=auth)
                self.assertEqual((await r.json())["ear"]["name"], "Home Assistant")

                now = time.time()
                r = await client.post("/api/ears/v1/heard", headers=auth, json={
                    "v": 1, "sent": now, "software": "test",
                    "heard": [item(at=now - 1, by="Kitchen", rssi=-70),
                              item(at=now - 1, by="Garage", rssi=-50),
                              item(mac="bad")]})
                self.assertEqual(await r.json(), {"taken": 2, "skipped": 1, "server_time": unittest.mock.ANY})

                devices, rows = ears.HUB.drain()
                for d in devices:
                    await db.upsert_device(mac=d.mac, friendly_name=d.name, rssi=d.rssi)
                await db.record_ear_heard(rows)

                r = await client.get("/api/device/C0:DE:00:00:00:01/ears")
                info = await r.json()
                self.assertTrue(info["has_ears"])
                self.assertEqual(info["live"][0]["listener"], "Garage")
                self.assertEqual({h["listener"] for h in info["history"]}, {"Kitchen", "Garage"})

                r = await client.get("/api/ears")
                listed = (await r.json())["ears"][0]
                self.assertEqual(listed["devices_today"], 1)
                self.assertEqual(listed["heard_total"], 2)
                self.assertTrue(listed["status"]["online"])

                await client.put(f"/api/ears/{created['id']}", json={"enabled": False})
                r = await client.post("/api/ears/v1/heard", headers=auth, json={"v": 1, "sent": now, "heard": []})
                self.assertEqual(r.status, 403)

                await client.delete(f"/api/ears/{created['id']}")
                r = await client.get("/api/ears/v1/hello", headers=auth)
                self.assertEqual(r.status, 401)


if __name__ == "__main__":
    unittest.main()
