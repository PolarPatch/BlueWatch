import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bluewatch.scanner import BluetoothScanner


def advertisement(rssi):
    return SimpleNamespace(
        rssi=rssi,
        local_name=None,
        service_uuids=[],
        manufacturer_data={},
        service_data={},
    )


class ScannerFreshnessTests(unittest.IsolatedAsyncioTestCase):
    async def test_snapshot_discards_stale_entries(self):
        scanner = BluetoothScanner()
        scanner._get_vendor = AsyncMock(return_value=None)
        scanner._live_ble = {
            "00:00:00:00:00:01": {
                "device": SimpleNamespace(address="00:00:00:00:00:01", name="fresh"),
                "adv": advertisement(-42),
                "seen_at": 71.0,
            },
            "00:00:00:00:00:02": {
                "device": SimpleNamespace(address="00:00:00:00:00:02", name="stale"),
                "adv": advertisement(-91),
                "seen_at": 69.0,
            },
        }

        with patch("bluewatch.scanner.time.monotonic", return_value=100.0):
            devices = await scanner._snapshot_ble_devices()

        self.assertEqual([device.mac for device in devices], ["00:00:00:00:00:01"])
        self.assertNotIn("00:00:00:00:00:02", scanner._live_ble)

    async def test_starting_new_session_clears_old_cache(self):
        scanner = BluetoothScanner()
        scanner._live_ble["00:00:00:00:00:01"] = {"seen_at": 1.0}
        fake_scanner = SimpleNamespace(start=AsyncMock())

        with patch("bluewatch.scanner.BleakScanner", return_value=fake_scanner):
            await scanner.start_continuous_ble()

        self.assertEqual(scanner._live_ble, {})
        self.assertIs(scanner._continuous_ble_scanner, fake_scanner)


if __name__ == "__main__":
    unittest.main()
