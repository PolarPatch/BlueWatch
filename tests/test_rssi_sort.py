import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bluewatch import db


class RssiSortTests(unittest.IsolatedAsyncioTestCase):
    async def test_latest_rssi_sort_keeps_missing_values_last(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(db, "DB_PATH", Path(directory) / "sort.db"):
                await db.init_db()
                async with db._connect() as connection:
                    await connection.executemany(
                        "INSERT INTO devices (mac, last_seen, total_sightings) VALUES (?, ?, 1)",
                        [
                            ("00:00:00:00:00:01", "2026-01-01T00:00:00"),
                            ("00:00:00:00:00:02", "2026-01-01T00:00:00"),
                            ("00:00:00:00:00:03", "2026-01-01T00:00:00"),
                        ],
                    )
                    await connection.executemany(
                        "INSERT INTO sightings (mac, timestamp, rssi) VALUES (?, ?, ?)",
                        [
                            ("00:00:00:00:00:01", "2026-01-01T00:00:00", -91),
                            ("00:00:00:00:00:02", "2026-01-01T00:00:00", -42),
                        ],
                    )
                    await connection.commit()

                ascending, _ = await db.get_devices_page(
                    page=1,
                    page_size=10,
                    show_all=True,
                    sort_column="rssi",
                    sort_direction="asc",
                )
                descending, _ = await db.get_devices_page(
                    page=1,
                    page_size=10,
                    show_all=True,
                    sort_column="rssi",
                    sort_direction="desc",
                )

        self.assertEqual(
            [(device.mac, device.last_rssi) for device in ascending],
            [
                ("00:00:00:00:00:01", -91),
                ("00:00:00:00:00:02", -42),
                ("00:00:00:00:00:03", None),
            ],
        )
        self.assertEqual(
            [(device.mac, device.last_rssi) for device in descending],
            [
                ("00:00:00:00:00:02", -42),
                ("00:00:00:00:00:01", -91),
                ("00:00:00:00:00:03", None),
            ],
        )


if __name__ == "__main__":
    unittest.main()
