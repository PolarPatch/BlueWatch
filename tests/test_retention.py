"""Forgetting device records that have not been seen for a while."""

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from bluewatch import db


class ForgetInactiveTests(unittest.IsolatedAsyncioTestCase):
    async def test_forgets_old_unmarked_devices_only(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(db, "DB_PATH", Path(directory) / "f.db"):
            await db.init_db()
            old = (datetime.now() - timedelta(days=40)).isoformat()
            macs = {
                "plain": "AA:00:00:00:00:01",
                "recent": "AA:00:00:00:00:02",
                "watched": "AA:00:00:00:00:03",
                "named": "AA:00:00:00:00:04",
                "noted": "AA:00:00:00:00:05",
                "grouped": "AA:00:00:00:00:06",
                "identity": "AA:00:00:00:00:07",
            }
            for mac in macs.values():
                await db.upsert_device(mac=mac, rssi=-60)
            async with db._connect() as conn:
                await conn.execute("INSERT INTO device_groups (name) VALUES ('Home')")
                for key, mac in macs.items():
                    if key == "recent":
                        continue
                    await conn.execute("UPDATE devices SET last_seen = ? WHERE mac = ?", (old, mac))
                    await conn.execute("INSERT INTO sightings (mac, timestamp, rssi) VALUES (?, ?, -70)", (mac, old))
                await conn.execute("UPDATE devices SET watched = 1 WHERE mac = ?", (macs["watched"],))
                await conn.execute("UPDATE devices SET friendly_name = 'Car' WHERE mac = ?", (macs["named"],))
                await conn.execute("UPDATE devices SET notes = 'x' WHERE mac = ?", (macs["noted"],))
                await conn.execute("UPDATE devices SET group_id = 1 WHERE mac = ?", (macs["grouped"],))
                await conn.execute("UPDATE devices SET identity_id = 1 WHERE mac = ?", (macs["identity"],))
                await conn.commit()

            self.assertEqual(await db.forget_inactive_devices(0), 0)
            self.assertEqual(await db.forget_inactive_devices(30), 1)
            async with db._connect() as conn:
                async with conn.execute("SELECT mac FROM devices") as cur:
                    left = {r[0] for r in await cur.fetchall()}
                async with conn.execute("SELECT COUNT(*) FROM sightings WHERE mac = ?", (macs["plain"],)) as cur:
                    plain_sightings = (await cur.fetchone())[0]
            self.assertEqual(left, set(macs.values()) - {macs["plain"]})
            self.assertEqual(plain_sightings, 0)

    async def test_setting_round_trips(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(db, "DB_PATH", Path(directory) / "s.db"):
            await db.init_db()
            settings = await db.get_settings()
            settings.device_retention_days = 30
            await db.update_settings(settings)
            self.assertEqual((await db.get_settings()).device_retention_days, 30)


if __name__ == "__main__":
    unittest.main()
