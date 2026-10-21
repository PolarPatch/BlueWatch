"""Timestamps for the outside world: every instant BlueWatch hands out carries
an explicit UTC offset (a trailing Z), so a browser in another timezone
works out the same age (#10).

The database keeps what it always had: naive timestamps written with
datetime.now(), in the server's local time. Nothing is rewritten. They are
read as local time when they leave through the API, an export or the
socket, using the timezone rules for that date, so daylight saving is
handled for old values too. BLUEWATCH_TIMEZONE (an IANA name such as
Europe/Oslo) overrides the system zone, for example in a container that
runs in UTC on a host that does not.

A few columns are filled by SQLite's CURRENT_TIMESTAMP, which is UTC. Their
readers mark them with utc_naive() so they are not shifted a second time.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone, tzinfo
from typing import Any, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import config

logger = logging.getLogger(__name__)

_NAIVE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d{1,6})?)?$")
_UNSET = object()
_zone: Any = _UNSET


def server_zone() -> Optional[tzinfo]:
    """The zone naive stored values were written in: BLUEWATCH_TIMEZONE if it
    names a real zone, else None, meaning the system's local time."""
    global _zone
    if _zone is _UNSET:
        _zone = None
        name = (config.TIMEZONE or "").strip()
        if name:
            try:
                _zone = ZoneInfo(name)
            except (ZoneInfoNotFoundError, ValueError):
                logger.warning("BLUEWATCH_TIMEZONE %r is not a known timezone; using the system's", name)
    return _zone


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _attach(value: datetime, fold: int) -> datetime:
    zone = server_zone()
    value = value.replace(fold=fold)
    return (value.replace(tzinfo=zone) if zone else value.astimezone()).astimezone(timezone.utc)


def local_to_utc(value: datetime) -> datetime:
    """A naive local datetime as an aware UTC one. Aware values pass through.

    When the clocks go back, an hour of local times happens twice and a
    naive value cannot say which. During that second hour, and for an hour
    after, a value that fits the second pass is read as the second pass, so
    a device seen just now does not show as an hour ago. Older ambiguous
    values are read as the first pass."""
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc)
    first, second = _attach(value, 0), _attach(value, 1)
    if first != second:
        age = (datetime.now(timezone.utc) - second).total_seconds()
        if -5 <= age < 3600:
            return second
    return first


def to_iso(value: Any) -> Any:
    """A naive local timestamp (string or datetime) as ISO 8601 UTC with Z.
    Anything else, including values that already carry an offset, is
    returned unchanged."""
    if isinstance(value, datetime):
        return _iso_z(local_to_utc(value))
    if isinstance(value, str) and _NAIVE_RE.match(value):
        try:
            return _iso_z(local_to_utc(datetime.fromisoformat(value.replace(" ", "T"))))
        except ValueError:
            return value
    return value


def utc_naive(value: Any) -> Any:
    """A naive value that is already UTC (SQLite CURRENT_TIMESTAMP), with Z."""
    if isinstance(value, str) and _NAIVE_RE.match(value):
        try:
            return _iso_z(datetime.fromisoformat(value.replace(" ", "T")).replace(tzinfo=timezone.utc))
        except ValueError:
            return value
    return value


def from_client(value: str) -> datetime:
    """A time sent by a browser, as the naive local time the database uses.
    With an offset (what the dashboard sends) it is converted; without one
    it is taken as server local time, as before. Raises ValueError."""
    dt = datetime.fromisoformat(value.strip().replace(" ", "T").replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return dt
    zone = server_zone()
    return (dt.astimezone(zone) if zone else dt.astimezone()).replace(tzinfo=None)


# Fields people or devices type into. A name or note that happens to look
# like a timestamp is text, not a time.
FREE_TEXT_KEYS = frozenset({
    "name", "friendly_name", "notes", "label", "vendor", "ssid", "model",
    "group_name", "ear_name", "listener", "message", "title", "description",
    "query", "search",
})


def stamp(data: Any) -> Any:
    """to_iso() over every value in a JSON-ready structure. Keys are left
    alone, so tables keyed by time of day ("08:15") keep their keys, and so
    are the values of FREE_TEXT_KEYS."""
    if isinstance(data, dict):
        return {k: v if k in FREE_TEXT_KEYS else stamp(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [stamp(v) for v in data]
    return to_iso(data)
