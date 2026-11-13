"""Band monitor for the RTL-SDR: noise floor and traffic per hopped
frequency (433.92, 868.3, 868.95 MHz ...), and an alert when a band's
noise floor stays far above its normal level -- what a car-key or alarm
jammer looks like from a fixed receiver. Receive only.

Nothing extra runs for this: rtl_433 itself reports its estimated noise
level (`-M noise`) and, with `-F log -v`, each retune ("Tuned to
868.300MHz."), so every noise reading can be put on the right frequency
while rtl_433 keeps decoding as before. The idea (watch the spectrum of
a fixed receiver for occupancy and interference) comes from OnAir's
spectrum tools; no code from it is used.
"""

import re
import statistics
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

BUCKET_MINUTES = 5
HISTORY_HOURS = 24 * 7
BASELINE_HOURS = 24
BASELINE_SKIP_MINUTES = 30       # the newest buckets are not part of "normal"
MIN_BASELINE_BUCKETS = 12        # an hour of data before anything alerts
HYSTERESIS_DB = 3.0
NOISE_INTERVAL_SECONDS = 5

_TUNED_RE = re.compile(r"Tuned to ([0-9.]+)\s*MHz", re.I)
_NOISE_RE = re.compile(r"Current noise level (-?[0-9.]+) dB", re.I)


def freq_label(mhz: float) -> str:
    return f"{mhz:.3f}".rstrip("0").rstrip(".")


def parse_freq(value) -> Optional[float]:
    """433.92 / "433.92M" / "868.3MHz" / 433920000 -> MHz."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        mhz = float(value)
    else:
        m = re.match(r"\s*([0-9.]+)\s*([kKmMgG]?)", str(value))
        if not m:
            return None
        mhz = float(m.group(1))
        unit = m.group(2).lower()
        if unit == "k":
            mhz /= 1000
        elif unit == "g":
            mhz *= 1000
        elif unit == "" and mhz > 1e5:
            mhz /= 1e6
    if mhz > 1e5:
        mhz /= 1e6
    return round(mhz, 3) if mhz > 0 else None


@dataclass
class Bucket:
    start: datetime
    levels: list = field(default_factory=list)
    decodes: int = 0

    def row(self) -> dict:
        return {
            "start": self.start,
            "avg": round(statistics.fmean(self.levels), 1) if self.levels else None,
            "max": round(max(self.levels), 1) if self.levels else None,
            "n": len(self.levels),
            "decodes": self.decodes,
        }


@dataclass
class Event:
    freq: str
    started: datetime
    baseline: float
    peak: float
    ended: Optional[datetime] = None
    alerted: bool = False

    @property
    def delta(self) -> float:
        return round(self.peak - self.baseline, 1)

    def as_dict(self) -> dict:
        return {
            "freq": self.freq,
            "started": self.started,
            "ended": self.ended,
            "baseline": round(self.baseline, 1),
            "peak": round(self.peak, 1),
            "delta": self.delta,
        }


class Band:
    def __init__(self, freq: str):
        self.freq = freq
        self.history: deque = deque(maxlen=HISTORY_HOURS * 60 // BUCKET_MINUTES)
        self.bucket: Optional[Bucket] = None
        self.last_level: Optional[float] = None
        self.last_at: Optional[datetime] = None
        self.elevated_since: Optional[datetime] = None
        self.event: Optional[Event] = None
        self.baseline: Optional[float] = None

    def _bucket_for(self, now: datetime) -> list[dict]:
        """Rolls the current bucket over when `now` is past it; returns the
        finished bucket rows (for storage)."""
        start = now.replace(second=0, microsecond=0)
        start -= timedelta(minutes=start.minute % BUCKET_MINUTES)
        done = []
        if self.bucket is None or self.bucket.start != start:
            if self.bucket is not None and (self.bucket.levels or self.bucket.decodes):
                row = self.bucket.row()
                self.history.append(row)
                done.append(row)
                self._update_baseline(now)
            self.bucket = Bucket(start)
        return done

    def _update_baseline(self, now: datetime) -> None:
        lo = now - timedelta(hours=BASELINE_HOURS)
        hi = now - timedelta(minutes=BASELINE_SKIP_MINUTES)
        vals = [r["avg"] for r in self.history if r["avg"] is not None and lo <= r["start"] <= hi]
        self.baseline = statistics.median(vals) if len(vals) >= MIN_BASELINE_BUCKETS else None

    def decodes_since(self, since: datetime) -> int:
        n = sum(r["decodes"] for r in self.history if r["start"] >= since)
        if self.bucket is not None and self.bucket.start >= since:
            n += self.bucket.decodes
        return n


class BandMonitor:
    """Fed line by line from rtl_433's stdout (non-JSON lines) and with each
    decode's frequency. All times are naive local, like the rest of the DB."""

    def __init__(self) -> None:
        self.bands: dict[str, Band] = {}
        self.plan: list[str] = []
        self.current: Optional[str] = None
        self._fresh_tune = False
        self.events: deque = deque(maxlen=50)
        self.pending_rows: list[tuple[str, dict]] = []   # finished buckets not yet stored
        self.pending_events: list[Event] = []            # opened/closed events not yet stored/alerted
        self.running = False

    # -- setup -----------------------------------------------------------

    def set_plan(self, freqs: list[str]) -> None:
        """The frequencies rtl_433 now hops. The first is tuned first."""
        labels = []
        for f in freqs:
            mhz = parse_freq(f)
            if mhz:
                labels.append(freq_label(mhz))
        self.plan = labels
        for label in labels:
            self.bands.setdefault(label, Band(label))
        self.current = labels[0] if len(labels) == 1 else None
        self._fresh_tune = True
        self.running = bool(labels)

    def stopped(self) -> None:
        self.running = False
        self.current = None

    def load_history(self, rows: list[dict], now: datetime) -> None:
        """Stored buckets (oldest first) so "normal" survives a restart."""
        for r in rows:
            band = self.bands.setdefault(r["freq"], Band(r["freq"]))
            band.history.append({k: r[k] for k in ("start", "avg", "max", "n", "decodes")})
        for band in self.bands.values():
            band._update_baseline(now)

    def _band(self, freq: Optional[str]) -> Optional[Band]:
        if freq is None:
            return None
        if freq in self.bands:
            return self.bands[freq]
        # A decode's own frequency is a little off the tuned one.
        mhz = parse_freq(freq)
        best = None
        for label in self.plan or list(self.bands):
            d = abs(float(label) - mhz) if mhz else 99
            if d <= 0.5 and (best is None or d < best[0]):
                best = (d, label)
        return self.bands[best[1]] if best else None

    # -- input -----------------------------------------------------------

    def log_line(self, line: str, now: datetime) -> None:
        m = _TUNED_RE.search(line)
        if m:
            mhz = parse_freq(m.group(1))
            if mhz:
                label = freq_label(mhz)
                self.bands.setdefault(label, Band(label))
                self.current = label
                self._fresh_tune = True
            return
        m = _NOISE_RE.search(line)
        if m:
            if self._fresh_tune:
                # The first reading after a retune still has the old band in it.
                self._fresh_tune = False
                return
            self.noise(float(m.group(1)), now)

    def noise(self, level: float, now: datetime) -> None:
        band = self._band(self.current)
        if band is None:
            return
        for row in band._bucket_for(now):
            self.pending_rows.append((band.freq, row))
        band.bucket.levels.append(level)
        band.last_level = level
        band.last_at = now
        self._judge(band, level, now)

    def decode(self, freq, now: datetime) -> None:
        mhz = parse_freq(freq)
        band = self._band(freq_label(mhz) if mhz else self.current)
        if band is None:
            return
        for row in band._bucket_for(now):
            self.pending_rows.append((band.freq, row))
        band.bucket.decodes += 1

    # -- jamming ---------------------------------------------------------

    threshold_db: float = 10     # set from Settings by the daemon
    min_minutes: float = 2

    def _judge(self, band: Band, level: float, now: datetime) -> None:
        base = band.baseline
        if base is None:
            band.elevated_since = None
            return
        high = level >= base + self.threshold_db
        low = level < base + self.threshold_db - HYSTERESIS_DB
        if high:
            if band.elevated_since is None:
                band.elevated_since = now
            if band.event is None and now - band.elevated_since >= timedelta(minutes=self.min_minutes):
                band.event = Event(band.freq, band.elevated_since, base, level)
                self.events.appendleft(band.event)
                self.pending_events.append(band.event)
            elif band.event is not None:
                band.event.peak = max(band.event.peak, level)
        elif low:
            band.elevated_since = None
            if band.event is not None:
                band.event.ended = now
                self.pending_events.append(band.event)
                band.event = None

    def take_rows(self) -> list[tuple[str, dict]]:
        rows, self.pending_rows = self.pending_rows, []
        return rows

    def take_events(self) -> list[Event]:
        evs, self.pending_events = self.pending_events, []
        return evs

    # -- output ----------------------------------------------------------

    def state(self, band: Band, now: datetime) -> str:
        if band.event is not None:
            return "jammed"
        if band.baseline is None:
            return "learning"
        if band.last_level is not None and band.last_level >= band.baseline + self.threshold_db:
            return "elevated"
        return "normal"

    def snapshot(self, now: datetime, hours: int = 24) -> dict:
        since = now - timedelta(hours=hours)
        hour_ago = now - timedelta(hours=1)
        order = self.plan + sorted(f for f in self.bands if f not in self.plan)
        out = []
        for freq in order:
            band = self.bands[freq]
            hist = [r for r in band.history if r["start"] >= since]
            if band.bucket is not None and band.bucket.start >= since:
                hist = hist + [band.bucket.row()]
            stale = band.last_at is None or now - band.last_at > timedelta(minutes=10)
            out.append({
                "freq": freq,
                "hopped": freq in self.plan and self.running,
                "tuned": freq == self.current and self.running,
                "level": None if stale else band.last_level,
                "baseline": round(band.baseline, 1) if band.baseline is not None else None,
                "delta": (round(band.last_level - band.baseline, 1)
                          if not stale and band.baseline is not None and band.last_level is not None else None),
                "state": "idle" if stale and not band.event else self.state(band, now),
                "decodes_1h": band.decodes_since(hour_ago),
                "history": hist,
            })
        return {
            "running": self.running,
            "threshold_db": self.threshold_db,
            "min_minutes": self.min_minutes,
            "bucket_minutes": BUCKET_MINUTES,
            "bands": out,
            "events": [e.as_dict() for e in self.events],
        }


BAND = BandMonitor()
