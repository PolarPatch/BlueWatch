"""Crowd: a rough count of the people around, from the Bluetooth BlueWatch
already hears. Nothing new is stored about anyone: the count is worked out
from the sightings table in 5-minute buckets, and only the totals are kept.

The idea of counting people by their phones comes from ESP32-Paxcounter
(cyberman54, Apache-2.0). The method here is BlueWatch's own:

- Only devices people carry count: phones are the people, and phones plus
  watches, earbuds, wearables, glasses, tablets and laptops are "personal
  devices". Trackers, TVs, beacons and unknowns do not count.
- Only sightings at or above RSSI_FLOOR, so the count covers roughly the
  same radius as the radar's outer ring rather than the whole street.
- A phone changes its Bluetooth address every 15 minutes or so. Within a
  bucket, two addresses of the same type that never overlap in time and
  are about as loud are taken as one device that rotated.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import median
from typing import Iterable

BUCKET_CHOICES = (1, 5, 10)
DEFAULT_BUCKET = 5
RSSI_FLOOR = -80
ROTATION_RSSI_GAP = 8          # dB between the two halves of a rotation
PEOPLE_TYPES = frozenset({"phone"})
PERSONAL_TYPES = frozenset({"phone", "watch", "audio", "wearable", "glasses", "tablet", "laptop"})


@dataclass
class Span:
    first: float
    last: float
    rssi: float


def derotate(spans: list[Span]) -> int:
    """How many devices a set of address spans of one type most likely came
    from: chain each address onto an earlier one that had gone quiet before
    it appeared and was about as loud."""
    chains: list[Span] = []
    for span in sorted(spans, key=lambda s: s.first):
        best = None
        for chain in chains:
            if chain.last < span.first and abs(chain.rssi - span.rssi) <= ROTATION_RSSI_GAP:
                if best is None or chain.last > best.last:
                    best = chain
        if best is None:
            chains.append(Span(span.first, span.last, span.rssi))
        else:
            best.last, best.rssi = span.last, span.rssi
    return len(chains)


def estimate(rows: Iterable[tuple[str, float, int, str]]) -> dict:
    """rows: (mac, unix time, rssi, device type) for one bucket."""
    heard: dict[str, list[tuple[float, int]]] = defaultdict(list)
    types: dict[str, str] = {}
    for mac, at, rssi, dtype in rows:
        if rssi is None or rssi < RSSI_FLOOR or dtype not in PERSONAL_TYPES:
            continue
        heard[mac].append((at, rssi))
        types[mac] = dtype
    by_type: dict[str, list[Span]] = defaultdict(list)
    for mac, seen in heard.items():
        times = [t for t, _ in seen]
        by_type[types[mac]].append(Span(min(times), max(times), median(r for _, r in seen)))
    counts = {t: derotate(spans) for t, spans in by_type.items()}
    return {
        "people": sum(n for t, n in counts.items() if t in PEOPLE_TYPES),
        "devices": sum(counts.values()),
        "addresses": len(heard),
    }
