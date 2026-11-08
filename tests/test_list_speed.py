"""The stored randomized flag and the identity representative filter."""

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from bluewatch import db


class RandomizedColumnTests(unittest.IsolatedAsyncioTestCase):
    async def test_flag_set_on_insert_and_backfilled(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(db, "DB_PATH", Path(directory) / "r.db"):
            await db.init_db()
            await db.upsert_device(mac="00:11:22:00:00:01", rssi=-60)   # fixed
            await db.upsert_device(mac="4A:00:00:00:00:02", rssi=-60)   # randomized
            async with db._connect() as conn:
                rows = dict(await (await conn.execute("SELECT mac, randomized FROM devices")).fetchall())
                self.assertEqual(rows, {"00:11:22:00:00:01": 0, "4A:00:00:00:00:02": 1})
                # A row from before the column existed is fixed on the next start.
                await conn.execute("UPDATE devices SET randomized = 0")
                await conn.commit()
            await db.init_db()
            async with db._connect() as conn:
                value = (await (await conn.execute(
                    "SELECT randomized FROM devices WHERE mac = '4A:00:00:00:00:02'")).fetchone())[0]
            self.assertEqual(value, 1)
            rows, total = await db.get_devices_page(page=1, page_size=10, exclude_randomized=True)
            self.assertEqual([d.mac for d in rows], ["00:11:22:00:00:01"])
            stats = await db.get_dashboard_stats()
            self.assertEqual((stats["total"], stats["randomized_count"]), (1, 1))

    async def test_identity_shows_newest_address_only(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(db, "DB_PATH", Path(directory) / "i.db"):
            await db.init_db()
            now = datetime.now()
            macs = ["00:11:22:00:00:11", "00:11:22:00:00:12", "00:11:22:00:00:13"]
            for mac in macs:
                await db.upsert_device(mac=mac, rssi=-60)
            async with db._connect() as conn:
                for i, mac in enumerate(macs[:2]):
                    await conn.execute("UPDATE devices SET identity_id = 7, last_seen = ? WHERE mac = ?",
                                       ((now - timedelta(minutes=10 - i)).isoformat(), mac))
                await conn.commit()
            rows, total = await db.get_devices_page(page=1, page_size=10, exclude_randomized=True)
            self.assertEqual(sorted(d.mac for d in rows), ["00:11:22:00:00:12", "00:11:22:00:00:13"])
            self.assertEqual(total, 2)


if __name__ == "__main__":
    unittest.main()
