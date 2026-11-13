import unittest
from datetime import datetime, timedelta

from bluewatch import rfband


def _feed(mon, freq, level, start, minutes, step=5):
    mon.log_line(f"SDR: Tuned to {freq}MHz.", start)
    t = start
    mon.log_line(f"Auto Level: Current noise level {level} dB, estimated noise {level} dB", t)  # skipped (fresh tune)
    end = start + timedelta(minutes=minutes)
    while t < end:
        t += timedelta(seconds=step)
        mon.log_line(f"Auto Level: Current noise level {level} dB, estimated noise {level} dB", t)
    return t


class BandMonitorTest(unittest.TestCase):
    def setUp(self):
        self.mon = rfband.BandMonitor()
        self.mon.set_plan(["433.92M", "868.3M"])
        self.t0 = datetime(2026, 11, 13, 10, 0, 0)

    def test_parse_freq(self):
        self.assertEqual(rfband.parse_freq("433.92M"), 433.92)
        self.assertEqual(rfband.parse_freq("868300000"), 868.3)
        self.assertEqual(rfband.parse_freq(868.95), 868.95)
        self.assertEqual(rfband.parse_freq("912600k"), 912.6)
        self.assertEqual(rfband.freq_label(868.3), "868.3")

    def test_noise_goes_to_tuned_band_and_first_reading_is_skipped(self):
        self.mon.log_line("SDR: Tuned to 868.300MHz.", self.t0)
        self.mon.log_line("Auto Level: Current noise level -20.0 dB, estimated noise -33.7 dB", self.t0)
        self.mon.log_line("Auto Level: Current noise level -34.3 dB, estimated noise -34.3 dB", self.t0)
        self.assertEqual(self.mon.bands["868.3"].last_level, -34.3)
        self.assertIsNone(self.mon.bands["433.92"].last_level)

    def test_decode_counted_on_nearest_band(self):
        self.mon.decode(433.95, self.t0)
        self.mon.decode("868.27", self.t0)
        self.mon.decode(None, self.t0)  # no tuned band yet: dropped
        snap = self.mon.snapshot(self.t0 + timedelta(minutes=1))
        counts = {b["freq"]: b["decodes_1h"] for b in snap["bands"]}
        self.assertEqual(counts, {"433.92": 1, "868.3": 1})

    def test_learning_then_jamming_event(self):
        t = _feed(self.mon, "433.920", -32.4, self.t0, 90)
        band = self.mon.bands["433.92"]
        self.assertAlmostEqual(band.baseline, -32.4)
        self.assertGreater(len(self.mon.take_rows()), 10)
        # 1 min high: not yet
        t = _feed(self.mon, "433.920", -18.0, t, 1)
        self.assertEqual(self.mon.take_events(), [])
        # keeps going past min_minutes
        t = _feed(self.mon, "433.920", -17.0, t, 2)
        evs = self.mon.take_events()
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0].freq, "433.92")
        self.assertIsNone(evs[0].ended)
        self.assertGreaterEqual(evs[0].delta, 14)
        self.assertEqual(self.mon.snapshot(t)["bands"][0]["state"], "jammed")
        # back to normal closes it
        t = _feed(self.mon, "433.920", -32.0, t, 1)
        evs = self.mon.take_events()
        self.assertEqual(len(evs), 1)
        self.assertIsNotNone(evs[0].ended)
        self.assertEqual(self.mon.snapshot(t)["bands"][0]["state"], "normal")

    def test_no_alert_while_learning(self):
        t = _feed(self.mon, "433.920", -32.4, self.t0, 20)
        _feed(self.mon, "433.920", -10.0, t, 10)
        self.assertEqual(self.mon.take_events(), [])
        self.assertIsNone(self.mon.bands["433.92"].baseline)

    def test_other_band_dwell_does_not_reset(self):
        t = _feed(self.mon, "868.300", -34.3, self.t0, 90)
        t = _feed(self.mon, "868.300", -20.0, t, 1)
        t = _feed(self.mon, "433.920", -32.0, t, 1)   # hop away, quiet there
        t = _feed(self.mon, "868.300", -20.0, t, 1.2)
        evs = self.mon.take_events()
        self.assertEqual([e.freq for e in evs], ["868.3"])

    def test_load_history_sets_baseline(self):
        rows = [{"freq": "433.92", "start": self.t0 - timedelta(minutes=5 * i), "avg": -31.0,
                 "max": -30.0, "n": 10, "decodes": 0} for i in range(30, 6, -1)]
        self.mon.load_history(rows, self.t0)
        self.assertAlmostEqual(self.mon.bands["433.92"].baseline, -31.0)


if __name__ == "__main__":
    unittest.main()
