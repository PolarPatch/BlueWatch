#!/usr/bin/env python3
"""Pretend to be a remote ear, for trying out Config > Ears without any extra
hardware. Simulates a small house with three listeners and a handful of demo
devices; one of them ("Demo walker") wanders from room to room, so Device
Details shows the nearest listener changing.

Standard library only:

    python3 tools/fake_ear.py --hub http://localhost:8080 --token bwear_...

The demo devices use made-up static random addresses (C0:DE:xx:xx:xx:xx)
and names starting with "Demo", so they are easy to find and delete later.
"""

import argparse
import json
import math
import random
import time
import urllib.error
import urllib.request

ROOMS = {"Kitchen": (0.0, 0.0), "Living room": (8.0, 0.0), "Garage": (4.0, 9.0)}

DEVICES = [
    # mac, name, home position, payload extras
    ("C0:DE:00:00:00:01", "Demo fridge sensor", (0.5, 0.5), {"m": {"1177": "0101"}}),
    ("C0:DE:00:00:00:02", "Demo TV", (7.5, 1.0), {"u": ["fe9f"]}),
    ("C0:DE:00:00:00:03", "Demo car tag", (4.5, 8.5), {"u": ["180f"]}),
    ("C0:DE:00:00:00:04", "Demo headphones", (6.0, 2.0), {"s": {"fe2c": "0a0b0c"}}),
    ("C0:DE:00:00:00:05", "Demo walker", None, {"u": ["180d"]}),
]


def walker_position(t: float) -> tuple[float, float]:
    """A slow loop through all three rooms, about four minutes per round."""
    stops = list(ROOMS.values())
    phase = (t / 80.0) % len(stops)
    i = int(phase)
    a, b = stops[i], stops[(i + 1) % len(stops)]
    f = min(1.0, (phase - i) * 1.6)  # linger a while in each room
    return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f


def rssi_at(device: tuple[float, float], room: tuple[float, float]) -> int:
    d = max(0.5, math.dist(device, room))
    return int(round(-50 - 22 * math.log10(d) + random.gauss(0, 2.5)))


def batch(now: float) -> list[dict]:
    heard = []
    for mac, name, home, extra in DEVICES:
        pos = home or walker_position(now)
        for room, room_pos in ROOMS.items():
            rssi = rssi_at(pos, room_pos)
            if rssi < -92:
                continue  # out of earshot for this listener
            heard.append({"mac": mac, "name": name, "rssi": rssi, "by": room,
                          "at": now - random.uniform(0, 3), **extra})
    return heard


def call(url: str, token: str, body=None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET", headers={
        "Authorization": "Bearer " + token, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--hub", default="http://localhost:8080")
    parser.add_argument("--token", required=True)
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--rounds", type=int, default=0, help="stop after N batches (0 = run until Ctrl-C)")
    args = parser.parse_args()
    hub = args.hub.rstrip("/")
    try:
        hello = call(hub + "/api/ears/v1/hello", args.token)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Hub refused the token: {e.code} {e.read().decode(errors='replace')}")
    print(f"Connected to BlueWatch {hello['bluewatch']} as ear '{hello['ear']['name']}'")
    n = 0
    while True:
        now = time.time()
        reply = call(hub + "/api/ears/v1/heard", args.token,
                     {"v": 1, "sent": time.time(), "software": "fake_ear", "heard": batch(now)})
        wx, wy = walker_position(now)
        nearest = min(ROOMS, key=lambda r: math.dist((wx, wy), ROOMS[r]))
        print(f"sent {reply['taken']} (skipped {reply['skipped']}) · walker nearest {nearest}")
        n += 1
        if args.rounds and n >= args.rounds:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
