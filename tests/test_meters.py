"""Utility meters on rtl_433, and the Fieldwatch catalog 96 signatures."""

import unittest

from bluewatch import classifier, rtl433


def classify(**kwargs):
    return classifier.classify_device(None, **kwargs)


def uuid16(short):
    return f"0000{short}-0000-1000-8000-00805f9b34fb"


class MeterTests(unittest.TestCase):
    def test_region_adds_frequencies_and_rate(self):
        self.assertEqual(rtl433.hop_plan(["433.92M", "868.3M"], "off"), (["433.92M", "868.3M"], "1000k"))
        self.assertEqual(rtl433.hop_plan(["433.92M", "868.3M"], "eu"),
                         (["433.92M", "868.3M", "868.95M"], "1200k"))
        self.assertEqual(rtl433.hop_plan(["433.92M"], "na"), (["433.92M", "912.6M", "916.45M"], "1200k"))

    def test_readings_are_dropped(self):
        scm = {"model": "ERT-SCM", "id": 12345678, "ert_type": 7, "consumption_data": 4512, "rssi": -12.1}
        self.assertEqual(rtl433.meter_safe(scm), {"model": "ERT-SCM", "id": 12345678, "ert_type": 7, "rssi": -12.1})
        sparsnas = {"model": "Ikea-Sparsnas", "id": 600123, "power_W": 2310.0, "energy_kWh": 812.5}
        self.assertEqual(rtl433.meter_safe(sparsnas), {"model": "Ikea-Sparsnas", "id": 600123})
        weather = {"model": "Nexus-TH", "id": 1, "temperature_C": 7.5}
        self.assertEqual(rtl433.meter_safe(weather), weather)

    def test_idm_has_a_key(self):
        self.assertEqual(rtl433._device_key({"model": "IDM", "ERTSerialNumber": 99}), "RF:IDM:99")

    def test_meters_classified(self):
        for model in ("Wireless-MBus", "ERT-SCM", "IDM", "Neptune-R900", "Badger-ORION", "Efergy-e2CT"):
            self.assertEqual(classify(name=model), classifier.TYPE_METER, model)
        self.assertNotEqual(classify(name="Nexus-TH"), classifier.TYPE_METER)


class FieldwatchCatalog96Tests(unittest.TestCase):
    def test_service_uuids(self):
        self.assertEqual(classify(service_uuids=[uuid16("fe33")]), classifier.TYPE_TRACKER)
        self.assertEqual(classify(service_uuids=[uuid16("feee")]), classifier.TYPE_WEARABLE)
        self.assertEqual(classify(service_uuids=[uuid16("3080")]), classifier.TYPE_FLIPPER)

    def test_polar_names(self):
        self.assertEqual(classify(name="Polar H10 1A2B3C4D"), classifier.TYPE_WEARABLE)
        self.assertEqual(classify(name="Polar Vantage V2 5E6F7A8B"), classifier.TYPE_WATCH)
        self.assertNotIn(classify(name="Polaroid Now"), (classifier.TYPE_WATCH, classifier.TYPE_WEARABLE))

    def test_remote_id_system_message(self):
        message = bytearray(25)
        message[0] = 0x42                      # System message, protocol 2
        message[1] = 0x01 | (1 << 2)           # live GNSS operator, EU classification
        message[2:6] = int(59.9 * 1e7).to_bytes(4, "little", signed=True)
        message[6:10] = int(10.7 * 1e7).to_bytes(4, "little", signed=True)
        message[17] = (1 << 4) | 2             # Open category, class C1
        message[18:20] = int((120 + 1000) / 0.5).to_bytes(2, "little")
        payload = bytes([classifier.DRONE_REMOTE_ID_AD_APP_CODE, 0]) + bytes(message)
        result = classifier.decode_drone_remote_id({classifier.DRONE_REMOTE_ID_SERVICE_DATA_UUID: payload})
        self.assertEqual(result["operator_location"], "pilot (live GNSS)")
        self.assertEqual(result["eu_category"], "Open")
        self.assertEqual(result["eu_class"], "C1")
        self.assertEqual(result["operator_altitude_m"], 120.0)


if __name__ == "__main__":
    unittest.main()
