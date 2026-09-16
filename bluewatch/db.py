"""Database operations for bluewatch."""

import bisect
import json
import logging
import re
import statistics
import aiosqlite
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from . import rpa
from .config import DB_PATH, HEARTBEAT_URL, HEARTBEAT_INTERVAL, PRUNE_DAYS, PRUNE_MIN_SIGHTINGS

logger = logging.getLogger(__name__)


@dataclass
class Device:
    """Represents a Bluetooth device."""
    mac: str
    vendor: Optional[str] = None
    friendly_name: Optional[str] = None
    device_type: Optional[str] = None
    ignored: bool = False
    watched: bool = False  # Device of Interest
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    total_sightings: int = 0
    service_uuids: list[str] = None  # BLE service UUIDs for fingerprinting
    bt_type: str = "ble"  # "ble" or "classic"
    device_class: Optional[int] = None  # Classic BT device class
    manufacturer_data: dict = None  # company_id (int) -> raw payload bytes
    service_data: dict = None  # service UUID (str) -> raw payload bytes -- e.g. Fast Pair's 3-byte Model ID under 0xFE2C
    appearance: Optional[int] = None  # GAP Appearance (AD type 0x19) -- standardized Bluetooth SIG device-category code
    name_conflict_at: Optional[datetime] = None  # Last time this MAC advertised a different name than its stored one
    name_conflict_name: Optional[str] = None  # The conflicting name seen (stored name is left unchanged)
    apple_activity: Optional[dict] = None  # Latest decoded Apple Continuity "Nearby Info" snapshot (screen on/idle/driving) -- overwritten every sighting, not fill-once
    apple_activity_at: Optional[datetime] = None  # When apple_activity was last updated
    group_id: Optional[int] = None  # Device group (category or subcategory)
    notes: Optional[str] = None  # Operator notes
    new_device_notified: bool = True  # Whether new-device notification has been sent
    # Per-device notification overrides. None = inherit default (silent if
    # categorized via group_id, else normal Unknown-device behavior).
    # "off" | "always" | "temp" (temp uses the paired *_expires_at column;
    # once now() passes it, treat as if unset again -- reverts to default).
    notify_arrive: Optional[str] = None
    notify_arrive_expires_at: Optional[datetime] = None
    notify_depart: Optional[str] = None
    notify_depart_expires_at: Optional[datetime] = None
    last_rssi: Optional[int] = None  # RSSI of the most recent sighting (not a persisted column -- joined in per-query)
    identity_id: Optional[int] = None  # Links MAC-rotation siblings sharing an advertised name into one logical device
    identity_mac_count: Optional[int] = None  # Not persisted -- joined in per-query when identity_id is set
    identity_total_sightings: Optional[int] = None  # Not persisted -- SUM(total_sightings) across the identity's MACs
    identity_first_seen: Optional[datetime] = None  # Not persisted -- MIN(first_seen) across the identity's MACs

    def __post_init__(self):
        if self.service_uuids is None:
            self.service_uuids = []
        if self.manufacturer_data is None:
            self.manufacturer_data = {}
        if self.service_data is None:
            self.service_data = {}


@dataclass
class Sighting:
    """Represents a device sighting."""
    id: int
    mac: str
    timestamp: datetime
    rssi: Optional[int] = None


@dataclass
class DeviceGroup:
    """Represents a device group/category. parent_id is None for a
    top-level category, or points to another group's id to make this a
    subcategory (one level of nesting; not enforced beyond convention)."""
    id: int
    name: str
    color: str = "#3b82f6"  # Default blue
    icon: str = "📁"
    parent_id: Optional[int] = None


@dataclass
class Settings:
    """Application settings."""
    # Notification settings
    ntfy_topic: Optional[str] = None
    ntfy_enabled: bool = False
    notify_new_device: bool = False
    notify_watched_return: bool = True
    notify_watched_leave: bool = True
    watched_absence_minutes: int = 30  # Minutes before "left"
    watched_return_minutes: int = 5    # Minutes of absence before "return" triggers
    new_device_threshold_minutes: int = 0  # 0 = immediate, >0 = deferred
    # Operations settings
    heartbeat_url: Optional[str] = None       # None = disabled
    heartbeat_interval: int = 300             # seconds
    prune_days: int = 0                       # 0 = disabled
    prune_min_sightings: int = 0              # 0 = prune by age only (keep device records)
    web_port: Optional[int] = None            # None = use the --port CLI default (8080); takes effect on next restart
    # Authentication settings
    auth_enabled: bool = False
    auth_username: Optional[str] = None
    auth_password_hash: Optional[str] = None  # bcrypt hash


SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    mac TEXT PRIMARY KEY,
    vendor TEXT,
    friendly_name TEXT,
    device_type TEXT,
    ignored INTEGER DEFAULT 0,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    total_sightings INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sightings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    rssi INTEGER,
    FOREIGN KEY (mac) REFERENCES devices(mac)
);

CREATE TABLE IF NOT EXISTS device_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#3b82f6',
    icon TEXT DEFAULT '📁'
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS name_vendor_map (
    name TEXT PRIMARY KEY COLLATE NOCASE,
    vendor TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS identities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS irk_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    irk_hex TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wigle_lookup_cache (
    mac TEXT PRIMARY KEY,
    vendor TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sightings_mac_time ON sightings(mac, timestamp);
CREATE INDEX IF NOT EXISTS idx_sightings_timestamp ON sightings(timestamp);
CREATE INDEX IF NOT EXISTS idx_identities_name ON identities(name COLLATE NOCASE);
"""

_CANONICAL_MAC_GLOB = (
    "[0-9A-Fa-f][0-9A-Fa-f]:[0-9A-Fa-f][0-9A-Fa-f]:[0-9A-Fa-f][0-9A-Fa-f]:"
    "[0-9A-Fa-f][0-9A-Fa-f]:[0-9A-Fa-f][0-9A-Fa-f]:[0-9A-Fa-f][0-9A-Fa-f]"
)
_RANDOMIZED_SECOND_NIBBLES = ("2", "3", "6", "7", "a", "b", "e", "f")
_DEVICE_FILTER_TYPES = {
    "phone": ("phone",),
    "laptop": ("laptop", "computer"),
    "audio": ("audio", "speaker"),
    "smart": ("smart",),
    "unknown": ("unknown",),
}


# The daemon runs the scan loop, the web server, and the prune loop in a single
# event loop, but each call below opens its own connection (each in its own
# thread). Those connections contend for SQLite's single write lock, and WAL can
# silently fall back to rollback-journal mode on some Docker bind mounts (where
# reads also block writes). Give every connection a generous busy timeout so it
# waits for the lock instead of immediately raising "database is locked".
_DB_TIMEOUT_SECONDS = 30.0


def _connect() -> aiosqlite.Connection:
    """Open a database connection sharing a common busy timeout."""
    return aiosqlite.connect(DB_PATH, timeout=_DB_TIMEOUT_SECONDS)


async def _enable_wal(db: aiosqlite.Connection) -> None:
    """Enable WAL mode and warn loudly if SQLite silently falls back.

    WAL is far more resilient to corruption on an unclean shutdown than the
    default rollback journal. The PRAGMA can be accepted but silently fall back
    to 'delete'/'truncate' mode on some filesystems (notably certain Docker
    bind mounts) — which is exactly the condition that lets an interrupted write
    leave an index out of sync with its table. Read the mode back and surface
    the fallback so it is diagnosable rather than silent.
    """
    async with db.execute("PRAGMA journal_mode=WAL") as cursor:
        row = await cursor.fetchone()
    mode = (row[0] if row else "") or ""
    if mode.lower() != "wal":
        logger.warning(
            "SQLite journal_mode is %r, not 'wal' (WAL fallback). The database "
            "is more vulnerable to corruption on unclean shutdown; check the "
            "filesystem backing %s.", mode, DB_PATH,
        )


_TREE_PAGE_RE = re.compile(r"\btree\s+(\d+)\s+page\b", re.IGNORECASE)


async def _index_rootpages(db: aiosqlite.Connection) -> dict:
    """Map each b-tree root page number to its object type ('table'/'index').

    integrity_check reports page-level damage as "Tree N page M ..." where N is
    the b-tree's root page. Resolving N back to its type lets us tell index
    corruption (rebuildable) from table corruption (data loss) when the message
    itself doesn't name an index.
    """
    async with db.execute(
        "SELECT rootpage, type FROM sqlite_master WHERE rootpage IS NOT NULL"
    ) as cursor:
        return {row[0]: row[1] for row in await cursor.fetchall()}


def _is_index_only(problems: list, roots: dict) -> bool:
    """True only if every reported problem is confined to an index b-tree.

    A line is index-related if it names an index, or points at a "Tree N" whose
    root page belongs to an index. Anything ambiguous or table-related makes this
    return False so we refuse to auto-repair and advise a restore instead.
    """
    for problem in problems:
        for line in problem.splitlines():
            line = line.strip()
            if not line or line.startswith("***"):  # section header, not a fault
                continue
            if "index" in line.lower():
                continue
            match = _TREE_PAGE_RE.search(line)
            if match and roots.get(int(match.group(1))) == "index":
                continue
            return False
    return True


async def _check_and_repair_integrity(db: aiosqlite.Connection) -> None:
    """Verify integrity at startup and self-heal index-only corruption.

    SQLite index corruption (e.g. "wrong # of entries in index ...") is fully
    recoverable from the intact table data via REINDEX, with no data loss, so we
    rebuild automatically. Corruption that touches table/page data is NOT safely
    auto-repairable; we surface it loudly and leave the file untouched for manual
    recovery from a backup.
    """
    try:
        async with db.execute("PRAGMA integrity_check") as cursor:
            rows = await cursor.fetchall()
    except aiosqlite.DatabaseError as exc:
        logger.error(
            "Integrity check could not run (%s); the database may be severely "
            "corrupt. Restore %s from a backup.", exc, DB_PATH,
        )
        return

    problems = [r[0] for r in rows if r and r[0] != "ok"]
    if not problems:
        return

    sample = "; ".join(problems[:5])
    roots = await _index_rootpages(db)
    if not _is_index_only(problems, roots):
        logger.error(
            "Database corruption detected that is NOT index-only (%d issue(s)): "
            "%s. This is not safely auto-repairable; restore %s from a backup.",
            len(problems), sample, DB_PATH,
        )
        return

    logger.warning(
        "Index corruption detected (%d issue(s)); rebuilding indexes via "
        "REINDEX: %s", len(problems), sample,
    )
    try:
        await db.execute("REINDEX")
        await db.commit()
        async with db.execute("PRAGMA integrity_check") as cursor:
            rows = await cursor.fetchall()
    except aiosqlite.DatabaseError as exc:
        logger.error("REINDEX failed (%s); restore %s from a backup.", exc, DB_PATH)
        return

    remaining = [r[0] for r in rows if r and r[0] != "ok"]
    if remaining:
        logger.error(
            "Index rebuild did not fully repair the database; %d issue(s) "
            "remain: %s. Restore %s from a backup.",
            len(remaining), "; ".join(remaining[:5]), DB_PATH,
        )
    else:
        logger.info("Database integrity restored: REINDEX successful.")


async def init_db() -> None:
    """Initialize the database schema."""
    async with _connect() as db:
        await _enable_wal(db)
        await _check_and_repair_integrity(db)
        await db.executescript(SCHEMA)

        # Migrations for devices table columns
        migrations = [
            ("device_type", "TEXT"),
            ("watched", "INTEGER DEFAULT 0"),
            ("service_uuids", "TEXT"),
            ("bt_type", "TEXT DEFAULT 'ble'"),
            ("device_class", "INTEGER"),
            ("group_id", "INTEGER REFERENCES device_groups(id)"),
            ("notes", "TEXT"),
            ("new_device_notified", "INTEGER DEFAULT 1"),
            ("notify_arrive", "TEXT"),
            ("notify_arrive_expires_at", "TIMESTAMP"),
            ("notify_depart", "TEXT"),
            ("notify_depart_expires_at", "TIMESTAMP"),
            ("identity_id", "INTEGER REFERENCES identities(id)"),
            ("manufacturer_data", "TEXT"),
            ("service_data", "TEXT"),
            ("appearance", "INTEGER"),
            ("name_conflict_at", "TIMESTAMP"),
            ("name_conflict_name", "TEXT"),
            # Apple Continuity "Nearby Info" live activity snapshot (screen
            # on/idle/driving, decoded in classifier.decode_apple_activity)
            # -- unlike every other device column, this is OVERWRITTEN on
            # every sighting rather than filled once, since it reflects
            # transient state at the moment of that specific advertisement.
            ("apple_activity", "TEXT"),
            ("apple_activity_at", "TIMESTAMP"),
        ]

        for column, column_type in migrations:
            try:
                await db.execute(f"ALTER TABLE devices ADD COLUMN {column} {column_type}")
                await db.commit()
            except Exception:
                pass  # Column already exists

        group_migrations = [
            ("parent_id", "INTEGER REFERENCES device_groups(id)"),
        ]
        for column, column_type in group_migrations:
            try:
                await db.execute(f"ALTER TABLE device_groups ADD COLUMN {column} {column_type}")
                await db.commit()
            except Exception:
                pass  # Column already exists

        # devices.identity_id is looked up via 3 correlated subqueries on
        # every paginated device-list request (identity_mac_count/
        # identity_total_sightings/identity_first_seen) -- without an
        # index this degrades from milliseconds to well over a minute
        # once the devices table grows into the tens of thousands of
        # rows, since each subquery falls back to a full table scan.
        # Added after the column itself via ALTER TABLE above, so this
        # runs last to guarantee the column exists first.
        await db.execute("CREATE INDEX IF NOT EXISTS idx_devices_identity_id ON devices(identity_id)")

        await db.commit()


def _parse_device_row(row) -> Device:
    """Parse a database row into a Device object."""
    keys = row.keys()

    # Parse service_uuids from JSON
    service_uuids = []
    if "service_uuids" in keys and row["service_uuids"]:
        try:
            service_uuids = json.loads(row["service_uuids"])
        except (json.JSONDecodeError, TypeError):
            pass

    # Parse manufacturer_data from JSON (company_id -> hex string -> bytes)
    manufacturer_data = {}
    if "manufacturer_data" in keys and row["manufacturer_data"]:
        try:
            raw = json.loads(row["manufacturer_data"])
            manufacturer_data = {int(k): bytes.fromhex(v) for k, v in raw.items()}
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    # Parse service_data from JSON (service UUID -> hex string -> bytes)
    service_data = {}
    if "service_data" in keys and row["service_data"]:
        try:
            raw = json.loads(row["service_data"])
            service_data = {k: bytes.fromhex(v) for k, v in raw.items()}
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    apple_activity = None
    if "apple_activity" in keys and row["apple_activity"]:
        try:
            apple_activity = json.loads(row["apple_activity"])
        except (json.JSONDecodeError, TypeError):
            pass

    return Device(
        mac=row["mac"],
        vendor=row["vendor"],
        friendly_name=row["friendly_name"],
        device_type=row["device_type"] if "device_type" in keys else None,
        ignored=bool(row["ignored"]),
        watched=bool(row["watched"]) if "watched" in keys else False,
        first_seen=datetime.fromisoformat(row["first_seen"]) if row["first_seen"] else None,
        last_seen=datetime.fromisoformat(row["last_seen"]) if row["last_seen"] else None,
        total_sightings=row["total_sightings"],
        service_uuids=service_uuids,
        manufacturer_data=manufacturer_data,
        service_data=service_data,
        name_conflict_at=datetime.fromisoformat(row["name_conflict_at"]) if "name_conflict_at" in keys and row["name_conflict_at"] else None,
        name_conflict_name=row["name_conflict_name"] if "name_conflict_name" in keys else None,
        bt_type=row["bt_type"] if "bt_type" in keys and row["bt_type"] else "ble",
        device_class=row["device_class"] if "device_class" in keys else None,
        appearance=row["appearance"] if "appearance" in keys else None,
        group_id=row["group_id"] if "group_id" in keys else None,
        notes=row["notes"] if "notes" in keys else None,
        new_device_notified=bool(row["new_device_notified"]) if "new_device_notified" in keys else True,
        notify_arrive=row["notify_arrive"] if "notify_arrive" in keys else None,
        notify_arrive_expires_at=(
            datetime.fromisoformat(row["notify_arrive_expires_at"])
            if "notify_arrive_expires_at" in keys and row["notify_arrive_expires_at"] else None
        ),
        notify_depart=row["notify_depart"] if "notify_depart" in keys else None,
        notify_depart_expires_at=(
            datetime.fromisoformat(row["notify_depart_expires_at"])
            if "notify_depart_expires_at" in keys and row["notify_depart_expires_at"] else None
        ),
        last_rssi=row["last_rssi"] if "last_rssi" in keys else None,
        identity_id=row["identity_id"] if "identity_id" in keys else None,
        identity_mac_count=row["identity_mac_count"] if "identity_mac_count" in keys else None,
        identity_total_sightings=row["identity_total_sightings"] if "identity_total_sightings" in keys else None,
        identity_first_seen=(
            datetime.fromisoformat(row["identity_first_seen"])
            if "identity_first_seen" in keys and row["identity_first_seen"] else None
        ),
        apple_activity=apple_activity,
        apple_activity_at=(
            datetime.fromisoformat(row["apple_activity_at"])
            if "apple_activity_at" in keys and row["apple_activity_at"] else None
        ),
    )


async def get_device(mac: str) -> Optional[Device]:
    """Get a device by MAC address."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT d.*,
                (SELECT COUNT(*) FROM devices d2 WHERE d2.identity_id = d.identity_id) AS identity_mac_count
                FROM devices d WHERE d.mac = ?""",
            (mac,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return _parse_device_row(row)
            return None


async def get_all_devices(include_ignored: bool = True) -> list[Device]:
    """Get all devices."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM devices"
        if not include_ignored:
            query += " WHERE ignored = 0"
        query += " ORDER BY last_seen DESC"

        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [_parse_device_row(row) for row in rows]


def _is_randomized_mac(mac: str) -> bool:
    """Python-side equivalent of _randomized_mac_sql, for call sites (like
    upsert_device's auto-attach check) that already have the value in hand
    and don't need a SQL round-trip."""
    parts = mac.split(":")
    if len(parts) != 6 or any(len(p) != 2 for p in parts):
        return False
    return parts[0][1].lower() in _RANDOMIZED_SECOND_NIBBLES


def _randomized_mac_sql(column: str) -> str:
    """SQL expression for locally-administered (randomized) MAC addresses."""
    nibbles = ", ".join(f"'{n}'" for n in _RANDOMIZED_SECOND_NIBBLES)
    return (
        f"({column} GLOB '{_CANONICAL_MAC_GLOB}' "
        f"AND lower(substr({column}, 2, 1)) IN ({nibbles}))"
    )


def _build_device_query_filters(
    include_ignored: bool,
    device_filter: str,
    search: Optional[str],
    exclude_randomized: bool,
    group_ids: Optional[list] = None,
    show_all: bool = False,
    only_uncategorized: bool = False,
    active_within_seconds: Optional[int] = None,
) -> tuple[str, list]:
    """Build WHERE clause and parameters for device list queries.

    active_within_seconds, when given, restricts to devices last seen in
    that window (the "live/nearby now" view) and implies show_all -- a
    device currently in range is worth seeing regardless of category.

    group_ids, when given, restricts to devices whose group_id is in that
    set -- callers filtering by a category should pass that category's id
    plus its direct subcategories' ids so a click on a top-level category
    also picks up devices filed under its subcategories.

    show_all bypasses the default "uncategorized only" restriction below,
    for an explicit "show every device regardless of category" view --
    ignored if group_ids is also given (a specific category takes
    precedence).

    only_uncategorized is the explicit "hide categorized devices" toggle --
    unlike the default triage-queue restriction below (which a search term
    or show_all bypasses), this one always wins, so the user can focus on
    Unknown devices even while searching."""
    conditions: list[str] = []
    params: list = []

    if not include_ignored:
        conditions.append("d.ignored = 0")

    if exclude_randomized:
        conditions.append(f"NOT {_randomized_mac_sql('d.mac')}")

    filter_key = (device_filter or "all").strip().lower()
    if filter_key == "watched":
        conditions.append("d.watched = 1")
    elif filter_key in _DEVICE_FILTER_TYPES:
        filter_types = _DEVICE_FILTER_TYPES[filter_key]
        placeholders = ", ".join("?" for _ in filter_types)
        conditions.append(f"COALESCE(d.device_type, 'unknown') IN ({placeholders})")
        params.extend(filter_types)

    search_value = (search or "").strip()

    if only_uncategorized:
        conditions.append("d.group_id IS NULL")
    elif group_ids:
        placeholders = ", ".join("?" for _ in group_ids)
        conditions.append(f"d.group_id IN ({placeholders})")
        params.extend(group_ids)
    elif not show_all and not search_value and not active_within_seconds:
        # No explicit category selected and no search text -- the main
        # list is the triage queue, so once a device has been sorted into
        # any category it drops out of here and only shows up under that
        # category. A text search should always search everything so
        # nothing is hidden from the results.
        conditions.append("d.group_id IS NULL")

    if active_within_seconds:
        cutoff = (datetime.now() - timedelta(seconds=active_within_seconds)).isoformat()
        conditions.append("d.last_seen >= ?")
        params.append(cutoff)

    # Collapse identity-clustered MAC-rotation siblings to a single
    # representative row (the most recently seen MAC in the group) --
    # devices with no identity_id are unaffected.
    conditions.append(
        "(d.identity_id IS NULL OR d.mac = ("
        "SELECT mac FROM devices d2 WHERE d2.identity_id = d.identity_id "
        "ORDER BY d2.last_seen DESC, d2.mac DESC LIMIT 1))"
    )

    if search_value:
        wildcard = f"%{search_value}%"
        conditions.append(
            "(d.mac LIKE ? OR COALESCE(d.vendor, '') LIKE ? OR COALESCE(d.friendly_name, '') LIKE ?)"
        )
        params.extend([wildcard, wildcard, wildcard])

    where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    return where_clause, params


_DEVICE_SORT_MAP = {
    "class": "COALESCE(d.device_type, 'unknown')",
    "mac": "d.mac",
    "vendor": "COALESCE(d.vendor, '')",
    "identifier": "COALESCE(d.friendly_name, '')",
    "sightings": "d.total_sightings",
    "last_seen": "COALESCE(d.last_seen, '')",
    "rssi": "(SELECT s.rssi FROM sightings s WHERE s.mac = d.mac ORDER BY s.timestamp DESC LIMIT 1)",
    "group": "COALESCE(g.name, '')",
}


async def get_devices_page(
    page: int = 1,
    page_size: int = 50,
    include_ignored: bool = True,
    device_filter: str = "all",
    search: Optional[str] = None,
    sort_column: str = "last_seen",
    sort_direction: str = "desc",
    exclude_randomized: bool = True,
    group_ids: Optional[list] = None,
    show_all: bool = False,
    only_uncategorized: bool = False,
    active_within_seconds: Optional[int] = None,
) -> tuple[list[Device], int]:
    """Get a single page of devices and total count for the current query."""
    safe_page = max(1, page)
    safe_page_size = max(1, min(page_size, 500))
    offset = (safe_page - 1) * safe_page_size

    sort_expr = _DEVICE_SORT_MAP.get(sort_column, _DEVICE_SORT_MAP["last_seen"])
    direction = "ASC" if str(sort_direction).lower() == "asc" else "DESC"

    where_clause, params = _build_device_query_filters(
        include_ignored=include_ignored,
        device_filter=device_filter,
        search=search,
        exclude_randomized=exclude_randomized,
        group_ids=group_ids,
        show_all=show_all,
        active_within_seconds=active_within_seconds,
        only_uncategorized=only_uncategorized,
    )

    base_query = "FROM devices d LEFT JOIN device_groups g ON g.id = d.group_id"
    order_clause = f" ORDER BY {sort_expr} {direction}, d.mac ASC"

    async with _connect() as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            f"SELECT COUNT(*) AS total {base_query}{where_clause}",
            params,
        ) as cursor:
            count_row = await cursor.fetchone()
            total = int(count_row["total"]) if count_row else 0

        page_params = [*params, safe_page_size, offset]
        async with db.execute(
            f"""SELECT d.*,
                (SELECT s.rssi FROM sightings s WHERE s.mac = d.mac ORDER BY s.timestamp DESC LIMIT 1) AS last_rssi,
                (SELECT COUNT(*) FROM devices d2 WHERE d2.identity_id = d.identity_id) AS identity_mac_count,
                (SELECT SUM(d2.total_sightings) FROM devices d2 WHERE d2.identity_id = d.identity_id) AS identity_total_sightings,
                (SELECT MIN(d2.first_seen) FROM devices d2 WHERE d2.identity_id = d.identity_id) AS identity_first_seen
                {base_query}{where_clause}{order_clause} LIMIT ? OFFSET ?""",
            page_params,
        ) as cursor:
            rows = await cursor.fetchall()
            return ([_parse_device_row(row) for row in rows], total)


async def get_devices_export(
    include_ignored: bool = True,
    device_filter: str = "all",
    search: Optional[str] = None,
    sort_column: str = "last_seen",
    sort_direction: str = "desc",
    exclude_randomized: bool = True,
) -> list[Device]:
    """Return every device matching the query (no pagination), for CSV export."""
    sort_expr = _DEVICE_SORT_MAP.get(sort_column, _DEVICE_SORT_MAP["last_seen"])
    direction = "ASC" if str(sort_direction).lower() == "asc" else "DESC"

    where_clause, params = _build_device_query_filters(
        include_ignored=include_ignored,
        device_filter=device_filter,
        search=search,
        exclude_randomized=exclude_randomized,
        show_all=True,  # export is a deliberate, explicit action -- always a complete picture, categorized devices included
    )

    base_query = "FROM devices d LEFT JOIN device_groups g ON g.id = d.group_id"
    order_clause = f" ORDER BY {sort_expr} {direction}, d.mac ASC"

    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            f"SELECT d.* {base_query}{where_clause}{order_clause}",
            params,
        ) as cursor:
            rows = await cursor.fetchall()
            return [_parse_device_row(row) for row in rows]


async def get_sightings_for_export(
    macs: list[str],
    days: Optional[int] = None,
) -> list[dict]:
    """Return every raw sighting (mac, timestamp, rssi) for the given devices.

    This is the un-aggregated detail behind the device export: one record per
    actual contact, not a summary. ``days`` limits to the last N days when set;
    the default (None) exports the full history. Sightings are pulled in MAC
    chunks to stay within SQLite's bound-parameter limit on large exports and
    returned ordered by MAC then time.
    """
    if not macs:
        return []

    rows_out: list[dict] = []
    chunk = 400  # well under SQLite's default bound-parameter limit

    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        for start in range(0, len(macs), chunk):
            subset = macs[start:start + chunk]
            placeholders = ", ".join("?" for _ in subset)
            where = f"mac IN ({placeholders})"
            params: list = list(subset)
            if days is not None:
                where += " AND timestamp > datetime('now', ?)"
                params.append(f"-{days} days")

            async with db.execute(
                f"""
                SELECT mac, timestamp, rssi FROM sightings
                WHERE {where}
                ORDER BY mac ASC, timestamp ASC
                """,
                params,
            ) as cursor:
                async for row in cursor:
                    rows_out.append({
                        "mac": row["mac"],
                        "timestamp": row["timestamp"],
                        "rssi": row["rssi"],
                    })

    return rows_out


async def get_dashboard_stats(include_ignored: bool = True) -> dict:
    """Get dashboard stats and server-side filter counts without loading all rows."""
    now = datetime.now()
    today_start = datetime.combine(now.date(), datetime.min.time())
    one_hour_ago = now - timedelta(hours=1)

    randomized_sql = _randomized_mac_sql("d.mac")
    non_randomized_sql = f"NOT {randomized_sql}"
    where_clause = "" if include_ignored else "WHERE d.ignored = 0"

    query = f"""
        SELECT
            SUM(CASE WHEN {non_randomized_sql} THEN 1 ELSE 0 END) AS total,
            SUM(CASE WHEN {randomized_sql} THEN 1 ELSE 0 END) AS randomized_count,
            SUM(CASE WHEN {non_randomized_sql} AND d.last_seen >= ? THEN 1 ELSE 0 END) AS active_today,
            SUM(CASE WHEN {non_randomized_sql} AND d.first_seen >= ? THEN 1 ELSE 0 END) AS new_past_hour,
            SUM(CASE WHEN {non_randomized_sql} AND d.watched = 1 THEN 1 ELSE 0 END) AS watched_count,
            SUM(CASE WHEN {non_randomized_sql} AND COALESCE(d.device_type, 'unknown') = 'phone' THEN 1 ELSE 0 END) AS phone_count,
            SUM(CASE WHEN {non_randomized_sql} AND COALESCE(d.device_type, 'unknown') IN ('laptop', 'computer') THEN 1 ELSE 0 END) AS laptop_count,
            SUM(CASE WHEN {non_randomized_sql} AND COALESCE(d.device_type, 'unknown') IN ('audio', 'speaker') THEN 1 ELSE 0 END) AS audio_count,
            SUM(CASE WHEN {non_randomized_sql} AND COALESCE(d.device_type, 'unknown') = 'smart' THEN 1 ELSE 0 END) AS smart_count,
            SUM(CASE WHEN {non_randomized_sql} AND COALESCE(d.device_type, 'unknown') = 'unknown' THEN 1 ELSE 0 END) AS unknown_count
        FROM devices d
        {where_clause}
    """

    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, (today_start.isoformat(), one_hour_ago.isoformat())) as cursor:
            row = await cursor.fetchone()

    if not row:
        return {
            "total": 0,
            "randomized_count": 0,
            "active_today": 0,
            "new_past_hour": 0,
            "filter_counts": {"all": 0, "watched": 0, "phone": 0, "laptop": 0, "audio": 0, "smart": 0, "unknown": 0},
        }

    total = int(row["total"] or 0)
    filter_counts = {
        "all": total,
        "watched": int(row["watched_count"] or 0),
        "phone": int(row["phone_count"] or 0),
        "laptop": int(row["laptop_count"] or 0),
        "audio": int(row["audio_count"] or 0),
        "smart": int(row["smart_count"] or 0),
        "unknown": int(row["unknown_count"] or 0),
    }

    return {
        "total": total,
        "randomized_count": int(row["randomized_count"] or 0),
        "active_today": int(row["active_today"] or 0),
        "new_past_hour": int(row["new_past_hour"] or 0),
        "filter_counts": filter_counts,
    }


async def get_global_stats(include_ignored: bool = True) -> dict:
    """Get global device totals without loading full row data."""
    today_start = datetime.combine(datetime.now().date(), datetime.min.time()).isoformat()
    where_clause = "" if include_ignored else "WHERE ignored = 0"

    query = f"""
        SELECT
            COUNT(*) AS total_devices,
            SUM(CASE WHEN last_seen >= ? THEN 1 ELSE 0 END) AS active_today,
            SUM(total_sightings) AS total_sightings
        FROM devices
        {where_clause}
    """

    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, (today_start,)) as cursor:
            row = await cursor.fetchone()

    if not row:
        return {"total_devices": 0, "active_today": 0, "total_sightings": 0}

    return {
        "total_devices": int(row["total_devices"] or 0),
        "active_today": int(row["active_today"] or 0),
        "total_sightings": int(row["total_sightings"] or 0),
    }


async def get_live_stats(active_within_seconds: int, most_seen_limit: int = 5) -> dict:
    """Stats for the "nearby now" live view: how many devices are currently
    in range (last seen within the window), and the currently-active
    devices with the most sightings overall -- the ones that are always
    around, not just whichever has the strongest signal this instant."""
    cutoff = (datetime.now() - timedelta(seconds=active_within_seconds)).isoformat()

    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT COUNT(*) AS total_devices FROM devices") as cursor:
            total_row = await cursor.fetchone()

        async with db.execute(
            "SELECT COUNT(*) AS active_now FROM devices WHERE last_seen >= ?",
            (cutoff,),
        ) as cursor:
            active_row = await cursor.fetchone()

        # Two counts on purpose: the raw total includes privacy-randomized
        # MACs that rotate throughout the day (one physical device can look
        # like several "new" ones), while the fixed-only count is closer to
        # genuinely new physical devices -- showing both makes MAC rotation
        # visible rather than hiding it, which is useful in itself.
        today_start = datetime.combine(datetime.now().date(), datetime.min.time()).isoformat()
        async with db.execute(
            "SELECT COUNT(*) AS new_today FROM devices WHERE first_seen >= ?",
            (today_start,),
        ) as cursor:
            new_today_row = await cursor.fetchone()

        async with db.execute(
            f"SELECT COUNT(*) AS new_today_fixed FROM devices WHERE first_seen >= ? AND NOT {_randomized_mac_sql('mac')}",
            (today_start,),
        ) as cursor:
            new_today_fixed_row = await cursor.fetchone()

        async with db.execute(
            """
            SELECT mac, vendor, friendly_name, total_sightings
            FROM devices
            WHERE last_seen >= ?
            ORDER BY total_sightings DESC, last_seen DESC
            LIMIT ?
            """,
            (cutoff, most_seen_limit),
        ) as cursor:
            top_rows = await cursor.fetchall()

    most_seen = [
        {
            "mac": row["mac"],
            "vendor": row["vendor"],
            "friendly_name": row["friendly_name"],
            "total_sightings": row["total_sightings"],
        }
        for row in top_rows
        if row["total_sightings"]
    ]

    return {
        "total_devices": int(total_row["total_devices"] or 0) if total_row else 0,
        "active_now": int(active_row["active_now"] or 0) if active_row else 0,
        "new_today": int(new_today_row["new_today"] or 0) if new_today_row else 0,
        "new_today_fixed": int(new_today_fixed_row["new_today_fixed"] or 0) if new_today_fixed_row else 0,
        "most_seen": most_seen,
    }


async def upsert_device(
    mac: str,
    vendor: Optional[str] = None,
    friendly_name: Optional[str] = None,
    rssi: Optional[int] = None,
    service_uuids: Optional[list[str]] = None,
    bt_type: str = "ble",
    device_class: Optional[int] = None,
    manufacturer_data: Optional[dict] = None,
    service_data: Optional[dict] = None,
    appearance: Optional[int] = None,
) -> tuple[Device, bool]:
    """Insert or update a device and record a sighting.

    Returns tuple of (device, is_new) where is_new indicates first sighting.
    """
    from .classifier import identify_apple_model, decode_apple_activity
    from .fastpair_models import identify_fastpair_device

    now = datetime.now()
    uuids_json = json.dumps(service_uuids) if service_uuids else None
    mfg_json = (
        json.dumps({str(k): v.hex() for k, v in manufacturer_data.items()})
        if manufacturer_data else None
    )
    svc_data_json = (
        json.dumps({str(k): v.hex() for k, v in service_data.items()})
        if service_data else None
    )

    # AirPods/Beats broadcast a generic or empty local name, so Apple's
    # Continuity Proximity Pairing message (when present) is a better
    # source for friendly_name than the advertised name itself -- only
    # used as a fallback when there's no advertised name to use instead.
    apple_model = identify_apple_model(manufacturer_data) if manufacturer_data else None
    if not friendly_name and apple_model:
        friendly_name = apple_model[0]

    # Fast Pair devices broadcast a Model ID (service_data under 0xFE2C)
    # that resolves to an exact product name/manufacturer via the bundled
    # registry (fastpair_models.py) -- same only-fill-if-empty fallback
    # reasoning as the Apple model lookup above.
    fastpair_match = identify_fastpair_device(service_data) if service_data else None
    if fastpair_match:
        if not friendly_name:
            friendly_name = fastpair_match["name"]
        if not vendor and fastpair_match.get("manufacturer"):
            vendor = fastpair_match["manufacturer"]

    # Live activity snapshot (screen on/idle/driving, etc.) -- overwritten
    # on every sighting rather than filled once, since it's transient
    # state, not a fixed property of the device. None (not an Apple
    # Nearby Info advertisement this cycle) leaves the stored value alone
    # rather than clearing it, so it still reflects the last time we did see one.
    apple_activity = decode_apple_activity(manufacturer_data) if manufacturer_data else None
    apple_activity_json = json.dumps(apple_activity) if apple_activity else None

    # A cryptographic IRK match (if any key is configured and resolves this
    # address) is strictly stronger evidence than the advertised-name
    # heuristic below, so it's resolved first and takes precedence wherever
    # both would apply. Uses its own connection since it's a self-contained
    # read-mostly lookup, cheap even when no IRKs are configured (bails
    # immediately for non-randomized MACs).
    irk_identity_id = await resolve_irk_identity(mac)

    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        # Check if device exists
        async with db.execute("SELECT * FROM devices WHERE mac = ?", (mac,)) as cursor:
            existing = await cursor.fetchone()

        is_new = existing is None

        if existing:
            # Build update based on what we have
            updates = ["last_seen = ?", "total_sightings = total_sightings + 1"]
            params = [now.isoformat()]

            # Update friendly_name if we have one and device doesn't
            if friendly_name and not existing["friendly_name"]:
                updates.append("friendly_name = ?")
                params.append(friendly_name)
            elif friendly_name and existing["friendly_name"] and friendly_name != existing["friendly_name"]:
                # A single MAC address advertising a different name than it
                # did before is a real anomaly -- a device doesn't normally
                # rename itself mid-lifetime. Keep the original (sticky)
                # name as before, but record the conflicting name so it's
                # visible in the UI, e.g. as a possible spoofing/cloning
                # signal rather than silently ignored or silently swapped.
                updates.append("name_conflict_at = ?")
                params.append(now.isoformat())
                updates.append("name_conflict_name = ?")
                params.append(friendly_name)

            # Update vendor if we have one and device doesn't
            if vendor and not existing["vendor"]:
                updates.append("vendor = ?")
                params.append(vendor)
            elif not existing["vendor"]:
                # No vendor from this sighting (or OUI lookup never found
                # one) and none set yet -- check whether this device's
                # advertised name was previously taught to us via
                # set_device_vendor() (e.g. "P mesh" -> "Plejd"), so every
                # device sharing that name gets labeled automatically.
                lookup_name = friendly_name or existing["friendly_name"]
                if lookup_name:
                    async with db.execute(
                        "SELECT vendor FROM name_vendor_map WHERE name = ? COLLATE NOCASE",
                        (lookup_name,),
                    ) as cursor:
                        mapped = await cursor.fetchone()
                    if mapped:
                        updates.append("vendor = ?")
                        params.append(mapped["vendor"])

            # Update/merge service_uuids if we have new ones
            if service_uuids:
                existing_uuids = []
                if "service_uuids" in existing.keys() and existing["service_uuids"]:
                    try:
                        existing_uuids = json.loads(existing["service_uuids"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                # Merge UUIDs (keep unique)
                merged = list(set(existing_uuids + service_uuids))
                updates.append("service_uuids = ?")
                params.append(json.dumps(merged))

            # Update/merge manufacturer_data if we have new company IDs (or
            # updated payloads for ones we already had -- firmware can
            # rotate the bytes, e.g. an AirTag's rolling identifier).
            if manufacturer_data:
                existing_mfg = {}
                if "manufacturer_data" in existing.keys() and existing["manufacturer_data"]:
                    try:
                        raw = json.loads(existing["manufacturer_data"])
                        existing_mfg = {str(k): v for k, v in raw.items()}
                    except (json.JSONDecodeError, TypeError):
                        pass
                existing_mfg.update({str(k): v.hex() for k, v in manufacturer_data.items()})
                updates.append("manufacturer_data = ?")
                params.append(json.dumps(existing_mfg))

            # Same merge behavior for service_data (Fast Pair's Model ID
            # under 0xFE2C, Eddystone frames, etc.)
            if service_data:
                existing_svc_data = {}
                if "service_data" in existing.keys() and existing["service_data"]:
                    try:
                        raw = json.loads(existing["service_data"])
                        existing_svc_data = {str(k): v for k, v in raw.items()}
                    except (json.JSONDecodeError, TypeError):
                        pass
                existing_svc_data.update({str(k): v.hex() for k, v in service_data.items()})
                updates.append("service_data = ?")
                params.append(json.dumps(existing_svc_data))

            # Update bt_type if we got classic BT info for a device we only had BLE for
            existing_bt_type = existing["bt_type"] if "bt_type" in existing.keys() else "ble"
            if bt_type == "classic" and existing_bt_type == "ble":
                updates.append("bt_type = ?")
                params.append("both")
            elif bt_type == "ble" and existing_bt_type == "classic":
                updates.append("bt_type = ?")
                params.append("both")

            # Update device_class if we have it and didn't before
            existing_device_class = existing["device_class"] if "device_class" in existing.keys() else None
            if device_class and not existing_device_class:
                updates.append("device_class = ?")
                params.append(device_class)

            # Same -- fill appearance once, don't chase re-advertised values
            existing_appearance = existing["appearance"] if "appearance" in existing.keys() else None
            if appearance is not None and existing_appearance is None:
                updates.append("appearance = ?")
                params.append(appearance)

            # Unlike every field above, this one is deliberately overwritten
            # on every sighting that has one -- it's live state, not a
            # fixed property to fill once.
            if apple_activity_json is not None:
                updates.append("apple_activity = ?")
                params.append(apple_activity_json)
                updates.append("apple_activity_at = ?")
                params.append(now.isoformat())

            # An IRK match always wins over whatever identity_id (if any)
            # the device already had -- it's a proof, not a guess.
            existing_identity_id = existing["identity_id"] if "identity_id" in existing.keys() else None
            if irk_identity_id is not None and irk_identity_id != existing_identity_id:
                updates.append("identity_id = ?")
                params.append(irk_identity_id)

            params.append(mac)
            await db.execute(
                f"UPDATE devices SET {', '.join(updates)} WHERE mac = ?",
                params
            )
        else:
            insert_vendor = vendor
            if not insert_vendor and friendly_name:
                # No vendor from the OUI lookup -- check if this advertised
                # name was previously taught to us (see set_device_vendor()).
                async with db.execute(
                    "SELECT vendor FROM name_vendor_map WHERE name = ? COLLATE NOCASE",
                    (friendly_name,),
                ) as cursor:
                    mapped = await cursor.fetchone()
                if mapped:
                    insert_vendor = mapped["vendor"]

            # Insert new device
            await db.execute(
                """
                INSERT INTO devices (mac, vendor, friendly_name, first_seen, last_seen, total_sightings, service_uuids, bt_type, device_class, manufacturer_data, service_data, appearance, new_device_notified, apple_activity, apple_activity_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    mac, insert_vendor, friendly_name, now.isoformat(), now.isoformat(), uuids_json, bt_type,
                    device_class, mfg_json, svc_data_json, appearance,
                    apple_activity_json, now.isoformat() if apple_activity_json else None,
                )
            )

            if irk_identity_id is not None:
                # Cryptographic IRK match -- definitive, skip the guess below.
                await db.execute(
                    "UPDATE devices SET identity_id = ? WHERE mac = ?",
                    (irk_identity_id, mac),
                )
            elif friendly_name and _is_randomized_mac(mac):
                # Auto-attach to an existing identity: a brand-new randomized-MAC
                # device that advertises a name already clustered under an
                # identity is, in all likelihood, that same physical device
                # having rotated its address again. Non-randomized MACs are
                # deliberately excluded -- a shared name on a fixed/vendor MAC is
                # just as likely to be a genuinely different unit of the same
                # product, not a rotation of one physical device.
                async with db.execute(
                    "SELECT id FROM identities WHERE name = ? COLLATE NOCASE",
                    (friendly_name,),
                ) as cursor:
                    identity_row = await cursor.fetchone()
                if identity_row:
                    await db.execute(
                        "UPDATE devices SET identity_id = ? WHERE mac = ?",
                        (identity_row["id"], mac),
                    )
                else:
                    # No identity exists for this name yet -- this could
                    # still be the *first* rotation of a device whose
                    # earlier MAC is sitting there un-clustered (identities
                    # are otherwise only created via the manual merge UI).
                    # If another randomized-MAC device already shares this
                    # exact name and isn't in an identity of its own yet,
                    # spin up a new identity now and link both MACs into it
                    # -- this is what actually makes rotation auto-tracked
                    # from the second sighting onward instead of requiring
                    # a manual merge every time.
                    async with db.execute(
                        "SELECT mac FROM devices WHERE friendly_name = ? COLLATE NOCASE "
                        "AND mac != ? AND identity_id IS NULL LIMIT 1",
                        (friendly_name, mac),
                    ) as cursor:
                        sibling_row = await cursor.fetchone()
                    if sibling_row and _is_randomized_mac(sibling_row["mac"]):
                        cursor = await db.execute(
                            "INSERT INTO identities (name) VALUES (?)", (friendly_name,)
                        )
                        new_identity_id = cursor.lastrowid
                        await db.execute(
                            "UPDATE devices SET identity_id = ? WHERE mac IN (?, ?)",
                            (new_identity_id, mac, sibling_row["mac"]),
                        )

        # Record sighting
        await db.execute(
            "INSERT INTO sightings (mac, timestamp, rssi) VALUES (?, ?, ?)",
            (mac, now.isoformat(), rssi)
        )

        await db.commit()

    device = await get_device(mac)
    return device, is_new


async def set_friendly_name(mac: str, name: str) -> None:
    """Set a friendly name for a device."""
    async with _connect() as db:
        await db.execute(
            "UPDATE devices SET friendly_name = ? WHERE mac = ?",
            (name, mac)
        )
        await db.commit()


async def set_ignored(mac: str, ignored: bool) -> None:
    """Set whether a device is ignored."""
    async with _connect() as db:
        await db.execute(
            "UPDATE devices SET ignored = ? WHERE mac = ?",
            (1 if ignored else 0, mac)
        )
        await db.commit()


async def set_watched(mac: str, watched: bool) -> None:
    """Set whether a device is a Device of Interest (watched)."""
    async with _connect() as db:
        await db.execute(
            "UPDATE devices SET watched = ? WHERE mac = ?",
            (1 if watched else 0, mac)
        )
        await db.commit()


async def set_device_type(mac: str, device_type: str) -> None:
    """Set the device type for a device."""
    async with _connect() as db:
        await db.execute(
            "UPDATE devices SET device_type = ? WHERE mac = ?",
            (device_type, mac)
        )
        await db.commit()


async def set_device_vendor(mac: str, vendor: Optional[str]) -> None:
    """Manually set (or clear) a device's vendor, overriding whatever the
    automatic OUI lookup found (or didn't find). If the device belongs to
    an identity (merged MAC-rotation/cluster), the vendor is applied to
    every MAC in that identity, not just the one currently viewed --
    otherwise the label would only show up while that specific MAC happens
    to be the collapsed representative row.

    Also remembers name -> vendor in name_vendor_map when the device has an
    advertised name and a non-empty vendor is being set, so any OTHER
    device (now or found later) advertising that same name gets the vendor
    auto-applied too -- see _apply_name_vendor_hint(), called from
    upsert_device. E.g. teach it once that "P mesh" is Plejd, and every
    Plejd mesh switch anyone's scanner finds afterward is labeled without
    having to set it MAC by MAC."""
    vendor = vendor.strip() if vendor else None
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT identity_id, friendly_name FROM devices WHERE mac = ?", (mac,)
        ) as cursor:
            row = await cursor.fetchone()
        identity_id = row["identity_id"] if row else None
        friendly_name = row["friendly_name"] if row else None

        if identity_id:
            await db.execute(
                "UPDATE devices SET vendor = ? WHERE identity_id = ?",
                (vendor, identity_id)
            )
        else:
            await db.execute(
                "UPDATE devices SET vendor = ? WHERE mac = ?",
                (vendor, mac)
            )

        if friendly_name and vendor:
            await db.execute(
                "INSERT INTO name_vendor_map (name, vendor) VALUES (?, ?) "
                "ON CONFLICT(name) DO UPDATE SET vendor = excluded.vendor",
                (friendly_name, vendor)
            )

        await db.commit()


async def set_device_notes(mac: str, notes: Optional[str]) -> None:
    """Set operator notes for a device."""
    async with _connect() as db:
        await db.execute(
            "UPDATE devices SET notes = ? WHERE mac = ?",
            (notes if notes else None, mac)
        )
        await db.commit()


async def mark_new_device_notified(mac: str) -> None:
    """Mark a device's new-device notification as sent."""
    async with _connect() as db:
        await db.execute(
            "UPDATE devices SET new_device_notified = 1 WHERE mac = ?",
            (mac,)
        )
        await db.commit()


async def get_sightings(mac: str, days: int = 30) -> list[Sighting]:
    """Get sightings for a device within the last N days."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM sightings
            WHERE mac = ? AND timestamp > datetime('now', ?)
            ORDER BY timestamp DESC
            """,
            (mac, f"-{days} days")
        ) as cursor:
            rows = await cursor.fetchall()
            sightings = []
            for row in rows:
                if not isinstance(row["timestamp"], str):
                    continue  # Skip malformed rows (e.g. wrong column type affinity left over from a db recovery) rather than 500 the whole device page.
                sightings.append(Sighting(
                    id=row["id"],
                    mac=row["mac"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    rssi=row["rssi"],
                ))
            return sightings


async def get_hourly_distribution(mac: str, days: int = 30) -> dict[int, int]:
    """Get hourly distribution of sightings for pattern analysis."""
    async with _connect() as db:
        async with db.execute(
            """
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
            FROM sightings
            WHERE mac = ? AND timestamp > datetime('now', ?)
            GROUP BY hour
            ORDER BY hour
            """,
            (mac, f"-{days} days")
        ) as cursor:
            rows = await cursor.fetchall()
            return {int(row[0]): row[1] for row in rows}


async def get_daily_distribution(mac: str, days: int = 30) -> dict[int, int]:
    """Get daily distribution of sightings (0=Monday, 6=Sunday)."""
    async with _connect() as db:
        async with db.execute(
            """
            SELECT strftime('%w', timestamp) as day, COUNT(*) as count
            FROM sightings
            WHERE mac = ? AND timestamp > datetime('now', ?)
            GROUP BY day
            ORDER BY day
            """,
            (mac, f"-{days} days")
        ) as cursor:
            rows = await cursor.fetchall()
            # SQLite %w: 0=Sunday, 1=Monday... Convert to 0=Monday
            return {(int(row[0]) - 1) % 7: row[1] for row in rows}


async def get_daily_sightings(mac: str, days: int = 30) -> list[dict]:
    """Get daily sighting counts for timeline visualization."""
    async with _connect() as db:
        async with db.execute(
            """
            SELECT date(timestamp) as date, COUNT(*) as count, AVG(rssi) as avg_rssi
            FROM sightings
            WHERE mac = ? AND timestamp > datetime('now', ?)
            GROUP BY date(timestamp)
            ORDER BY date ASC
            """,
            (mac, f"-{days} days")
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "date": row[0],
                    "count": row[1],
                    "avg_rssi": round(row[2]) if row[2] else None,
                }
                for row in rows
            ]


async def cleanup_old_sightings(days: int = 90) -> int:
    """Remove sightings older than N days. Returns count deleted."""
    async with _connect() as db:
        cursor = await db.execute(
            "DELETE FROM sightings WHERE timestamp < datetime('now', ?)",
            (f"-{days} days",)
        )
        await db.commit()
        return cursor.rowcount


async def vacuum_if_fragmented(min_free_mb: float = 64.0) -> float:
    """VACUUM the database when it has accumulated free pages worth reclaiming.

    Deleting rows (e.g. pruning stale devices) frees pages inside the file but
    does not shrink the file on disk — only VACUUM does, by rewriting it. VACUUM
    is expensive and takes a brief exclusive lock, so we only run it once the
    freelist is large enough to be worth the cost. After a VACUUM the freelist
    drops back to ~0, so this self-throttles: it fires after a big prune and then
    stays quiet until fragmentation builds up again.

    Returns the approximate megabytes that were free before vacuuming (0.0 when
    skipped).
    """
    async with _connect() as db:
        async with db.execute("PRAGMA freelist_count") as cursor:
            free_pages = (await cursor.fetchone())[0]
        async with db.execute("PRAGMA page_size") as cursor:
            page_size = (await cursor.fetchone())[0]

        free_mb = free_pages * page_size / (1024 * 1024)
        if free_mb < min_free_mb:
            return 0.0

        # VACUUM cannot run inside a transaction; make sure none is open.
        await db.commit()
        await db.execute("VACUUM")
        return round(free_mb, 1)


async def prune_stale_devices(days: int, min_sightings: int) -> int:
    """Delete stale devices and all of their sightings.

    A device is pruned only when it has not been seen for more than `days`
    days AND has accumulated fewer than `min_sightings` total sightings.
    Watched devices (Devices of Interest) and devices assigned to any
    category are never pruned -- both are a deliberate "keep this" signal
    from the user, same as watching. The foreign key
    on sightings is not enforced by SQLite, so the sighting rows are removed
    explicitly. Returns the number of devices deleted.

    Deletions are done in small MAC batches, each committed on its own. On a
    large database a single bulk DELETE can hold the write lock for over a
    minute, which both freezes the scanner and trips the busy timeout when the
    scanner is actively writing — so the prune would throw and silently delete
    nothing. Short, frequently-committed transactions let the scanner interleave.
    """
    if days <= 0 or min_sightings <= 0:
        return 0

    async with _connect() as db:
        cutoff = f"-{days} days"
        async with db.execute(
            """
            SELECT mac FROM devices
            WHERE COALESCE(watched, 0) = 0
              AND group_id IS NULL
              AND last_seen < datetime('now', ?)
              AND total_sightings < ?
            """,
            (cutoff, min_sightings),
        ) as cursor:
            macs = [row[0] for row in await cursor.fetchall()]

        if not macs:
            return 0

        deleted = 0
        chunk = 400  # short transactions; also stays under SQLite's bound-param limit
        for start in range(0, len(macs), chunk):
            subset = macs[start:start + chunk]
            placeholders = ", ".join("?" for _ in subset)
            await db.execute(
                f"DELETE FROM sightings WHERE mac IN ({placeholders})", subset
            )
            cursor = await db.execute(
                f"DELETE FROM devices WHERE mac IN ({placeholders})", subset
            )
            await db.commit()
            deleted += cursor.rowcount
        return deleted


async def search_devices(
    mac_filter: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> list[dict]:
    """
    Search for devices by MAC and/or time range.
    Returns devices with sighting count in the specified range.
    """
    async with _connect() as db:
        db.row_factory = aiosqlite.Row

        # Build query based on filters
        if start_time or end_time:
            # Search by time range - find devices seen in that range
            conditions = []
            params = []

            if mac_filter:
                conditions.append("d.mac LIKE ?")
                params.append(f"%{mac_filter}%")

            if start_time:
                conditions.append("s.timestamp >= ?")
                params.append(start_time.isoformat())

            if end_time:
                conditions.append("s.timestamp <= ?")
                params.append(end_time.isoformat())

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = f"""
                SELECT d.*, COUNT(s.id) as range_sightings,
                       MIN(s.timestamp) as range_first,
                       MAX(s.timestamp) as range_last
                FROM devices d
                JOIN sightings s ON d.mac = s.mac
                WHERE {where_clause}
                GROUP BY d.mac
                ORDER BY range_sightings DESC
            """
        else:
            # Just MAC filter, no time range
            if mac_filter:
                query = """
                    SELECT *, total_sightings as range_sightings,
                           first_seen as range_first, last_seen as range_last
                    FROM devices
                    WHERE mac LIKE ? OR friendly_name LIKE ? OR vendor LIKE ?
                    ORDER BY last_seen DESC
                """
                params = [f"%{mac_filter}%", f"%{mac_filter}%", f"%{mac_filter}%"]
            else:
                query = """
                    SELECT *, total_sightings as range_sightings,
                           first_seen as range_first, last_seen as range_last
                    FROM devices
                    ORDER BY last_seen DESC
                """
                params = []

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "mac": row["mac"],
                    "vendor": row["vendor"],
                    "friendly_name": row["friendly_name"],
                    "device_type": row["device_type"] if "device_type" in row.keys() else None,
                    "device_class": row["device_class"] if "device_class" in row.keys() else None,
                    "group_id": row["group_id"] if "group_id" in row.keys() else None,
                    "ignored": bool(row["ignored"]),
                    "first_seen": row["first_seen"],
                    "last_seen": row["last_seen"],
                    "total_sightings": row["total_sightings"],
                    "range_sightings": row["range_sightings"],
                    "range_first": row["range_first"],
                    "range_last": row["range_last"],
                }
                for row in rows
            ]


# ============================================================================
# Settings Management
# ============================================================================

async def get_settings() -> Settings:
    """Get all application settings."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT key, value FROM settings") as cursor:
            rows = await cursor.fetchall()
            settings_dict = {row["key"]: row["value"] for row in rows}

    return Settings(
        ntfy_topic=settings_dict.get("ntfy_topic"),
        ntfy_enabled=settings_dict.get("ntfy_enabled", "0") == "1",
        notify_new_device=settings_dict.get("notify_new_device", "0") == "1",
        notify_watched_return=settings_dict.get("notify_watched_return", "1") == "1",
        notify_watched_leave=settings_dict.get("notify_watched_leave", "1") == "1",
        watched_absence_minutes=int(settings_dict.get("watched_absence_minutes", "30")),
        watched_return_minutes=int(settings_dict.get("watched_return_minutes", "5")),
        new_device_threshold_minutes=int(settings_dict.get("new_device_threshold_minutes", "0")),
        heartbeat_url=settings_dict.get("heartbeat_url", HEARTBEAT_URL),
        heartbeat_interval=int(settings_dict.get("heartbeat_interval", str(HEARTBEAT_INTERVAL))),
        prune_days=int(settings_dict.get("prune_days", str(PRUNE_DAYS))),
        prune_min_sightings=int(settings_dict.get("prune_min_sightings", str(PRUNE_MIN_SIGHTINGS))),
        web_port=(int(settings_dict["web_port"]) if settings_dict.get("web_port") else None),
        auth_enabled=settings_dict.get("auth_enabled", "0") == "1",
        auth_username=settings_dict.get("auth_username"),
        auth_password_hash=settings_dict.get("auth_password_hash"),
    )


async def set_setting(key: str, value: str) -> None:
    """Set a single setting value."""
    async with _connect() as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        await db.commit()


async def update_settings(settings: Settings) -> None:
    """Update all settings from a Settings object."""
    async with _connect() as db:
        settings_pairs = [
            ("ntfy_topic", settings.ntfy_topic or ""),
            ("ntfy_enabled", "1" if settings.ntfy_enabled else "0"),
            ("notify_new_device", "1" if settings.notify_new_device else "0"),
            ("notify_watched_return", "1" if settings.notify_watched_return else "0"),
            ("notify_watched_leave", "1" if settings.notify_watched_leave else "0"),
            ("watched_absence_minutes", str(settings.watched_absence_minutes)),
            ("watched_return_minutes", str(settings.watched_return_minutes)),
            ("new_device_threshold_minutes", str(settings.new_device_threshold_minutes)),
            ("heartbeat_url", settings.heartbeat_url or ""),
            ("heartbeat_interval", str(settings.heartbeat_interval)),
            ("prune_days", str(settings.prune_days)),
            ("prune_min_sightings", str(settings.prune_min_sightings)),
            ("web_port", str(settings.web_port) if settings.web_port else ""),
        ]
        for key, value in settings_pairs:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
        await db.commit()


async def update_auth_settings(
    enabled: bool,
    username: Optional[str] = None,
    password_hash: Optional[str] = None
) -> None:
    """Update authentication settings."""
    async with _connect() as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("auth_enabled", "1" if enabled else "0")
        )
        if username is not None:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("auth_username", username)
            )
        if password_hash is not None:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("auth_password_hash", password_hash)
            )
        await db.commit()


# ============================================================================
# Device Groups Management
# ============================================================================

async def get_groups() -> list[DeviceGroup]:
    """Get all device groups (top-level categories and subcategories alike;
    callers that need the tree shape should group by parent_id)."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM device_groups ORDER BY name") as cursor:
            rows = await cursor.fetchall()
            return [_parse_group_row(row) for row in rows]


def _parse_group_row(row) -> DeviceGroup:
    keys = row.keys()
    return DeviceGroup(
        id=row["id"],
        name=row["name"],
        color=row["color"] or "#3b82f6",
        icon=row["icon"] or "📁",
        parent_id=row["parent_id"] if "parent_id" in keys else None,
    )


async def get_group(group_id: int) -> Optional[DeviceGroup]:
    """Get a device group by ID."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM device_groups WHERE id = ?", (group_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return _parse_group_row(row) if row else None


async def create_group(
    name: str, color: str = "#3b82f6", icon: str = "📁", parent_id: Optional[int] = None
) -> DeviceGroup:
    """Create a new device group. Pass parent_id to create it as a
    subcategory of an existing top-level category."""
    async with _connect() as db:
        cursor = await db.execute(
            "INSERT INTO device_groups (name, color, icon, parent_id) VALUES (?, ?, ?, ?)",
            (name, color, icon, parent_id)
        )
        await db.commit()
        return DeviceGroup(id=cursor.lastrowid, name=name, color=color, icon=icon, parent_id=parent_id)


async def update_group(
    group_id: int, name: str, color: str, icon: str, parent_id: Optional[int] = None
) -> None:
    """Update a device group, including re-parenting it."""
    async with _connect() as db:
        await db.execute(
            "UPDATE device_groups SET name = ?, color = ?, icon = ?, parent_id = ? WHERE id = ?",
            (name, color, icon, parent_id, group_id)
        )
        await db.commit()


async def delete_group(group_id: int) -> None:
    """Delete a device group. Devices in it fall back to Unknown (group_id
    NULL); subcategories of it are promoted to top-level (parent_id NULL)
    rather than being deleted or orphaned."""
    async with _connect() as db:
        await db.execute(
            "UPDATE devices SET group_id = NULL WHERE group_id = ?",
            (group_id,)
        )
        await db.execute(
            "UPDATE device_groups SET parent_id = NULL WHERE parent_id = ?",
            (group_id,)
        )
        await db.execute("DELETE FROM device_groups WHERE id = ?", (group_id,))
        await db.commit()


async def set_device_group(mac: str, group_id: Optional[int]) -> None:
    """Assign a device to a group (or remove from group if None)."""
    async with _connect() as db:
        await db.execute(
            "UPDATE devices SET group_id = ? WHERE mac = ?",
            (group_id, mac)
        )
        await db.commit()


async def set_device_notify(
    mac: str, event: str, mode: Optional[str], hours: Optional[float] = None
) -> None:
    """Set a per-device notification override.

    event: "arrive" or "depart"
    mode: None (inherit default), "off", "always", or "temp"
    hours: required when mode == "temp" -- how many hours from now the
    override stays active before automatically reverting to the default.
    """
    if event not in ("arrive", "depart"):
        raise ValueError(f"invalid event: {event}")
    if mode not in (None, "off", "always", "temp"):
        raise ValueError(f"invalid mode: {mode}")

    expires_at = None
    if mode == "temp":
        if not hours or hours <= 0:
            raise ValueError("temp mode requires a positive hours value")
        expires_at = (datetime.now() + timedelta(hours=hours)).isoformat()

    mode_col = f"notify_{event}"
    expires_col = f"notify_{event}_expires_at"
    async with _connect() as db:
        # Pre-registering a "watch for this address" override on a MAC we
        # haven't actually seen yet (e.g. a known device's fixed address,
        # ahead of it ever broadcasting) is a legitimate use -- create a
        # bare placeholder row rather than requiring a prior sighting.
        await db.execute("INSERT OR IGNORE INTO devices (mac) VALUES (?)", (mac,))
        await db.execute(
            f"UPDATE devices SET {mode_col} = ?, {expires_col} = ? WHERE mac = ?",
            (mode, expires_at, mac)
        )
        await db.commit()


def notify_mode_active(mode: Optional[str], expires_at: Optional[datetime]) -> Optional[bool]:
    """Resolve a raw (mode, expires_at) pair to whether the override is
    currently active. Returns True (notify), False (explicitly silenced),
    or None (no override -- caller should fall back to the category/Unknown
    default). A "temp" override past its expiry is treated as None (lapsed
    back to default) -- callers that want to clear the stale columns should
    do so separately; this function is read-only."""
    if mode is None:
        return None
    if mode == "off":
        return False
    if mode == "always":
        return True
    if mode == "temp":
        if expires_at and datetime.now() < expires_at:
            return True
        return None  # lapsed
    return None


async def get_devices_with_notify_override() -> list[Device]:
    """Devices that have any per-device notify_arrive/notify_depart
    override set (used by the notification loop instead of scanning the
    whole device table every cycle)."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM devices WHERE notify_arrive IS NOT NULL OR notify_depart IS NOT NULL"
        ) as cursor:
            rows = await cursor.fetchall()
            return [_parse_device_row(row) for row in rows]


async def get_devices_by_group(group_id: int) -> list[Device]:
    """Get all devices in a group."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM devices WHERE group_id = ? ORDER BY last_seen DESC",
            (group_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [_parse_device_row(row) for row in rows]


# ============================================================================
# Identities (MAC-rotation clustering)
# ============================================================================
#
# BLE privacy addressing means a single physical device (an iPhone's Find My
# relay, a mesh node, etc.) resurfaces as a brand-new MAC every ~15 minutes.
# An "identity" groups several MAC addresses that are (almost certainly) the
# same physical device -- created by merging devices that share an advertised
# name, after which any NEW device sharing that same name gets auto-attached
# on first sighting (see upsert_device) so the clustering keeps working
# without the user re-merging every rotation forever.

async def find_identity_by_name(name: str) -> Optional[int]:
    """Case-insensitive exact-name lookup, used both by the manual merge
    endpoint (reuse an existing identity instead of creating a duplicate)
    and by the auto-attach path in upsert_device."""
    async with _connect() as db:
        async with db.execute(
            "SELECT id FROM identities WHERE name = ? COLLATE NOCASE", (name,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def merge_devices_into_identity(macs: list[str], name: str) -> int:
    """Merge the given MAC addresses into one identity, named `name`. Reuses
    an existing identity with that exact (case-insensitive) name if one
    exists, rather than creating a duplicate -- so merging a newly-noticed
    rotation sibling into an already-clustered name just extends the same
    identity. Returns the identity id."""
    if not macs:
        raise ValueError("no MAC addresses given")

    identity_id = await find_identity_by_name(name)
    async with _connect() as db:
        if identity_id is None:
            cursor = await db.execute(
                "INSERT INTO identities (name) VALUES (?)", (name,)
            )
            identity_id = cursor.lastrowid
        placeholders = ", ".join("?" for _ in macs)
        await db.execute(
            f"UPDATE devices SET identity_id = ? WHERE mac IN ({placeholders})",
            [identity_id, *macs],
        )
        await db.commit()
    return identity_id


async def unmerge_device(mac: str) -> None:
    """Detach a single MAC from whatever identity it's in (does not delete
    the identity itself, even if this was its last member -- an empty
    identity is harmless and simply won't match anything)."""
    async with _connect() as db:
        await db.execute("UPDATE devices SET identity_id = NULL WHERE mac = ?", (mac,))
        await db.commit()


async def get_identity_members(identity_id: int) -> list[Device]:
    """Every MAC address ever attached to this identity, most recently seen
    first -- powers the "click to see all MACs" drill-down."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM devices WHERE identity_id = ? ORDER BY last_seen DESC",
            (identity_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [_parse_device_row(row) for row in rows]


async def get_irk_keys() -> list[dict]:
    """All configured Identity Resolving Keys, most recently added first."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, label, irk_hex, created_at FROM irk_keys ORDER BY id DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def add_irk_key(label: str, irk_hex: str) -> int:
    """Store a new IRK (already validated/normalized hex, 32 chars) under a
    human-readable label. Returns the new row's id."""
    async with _connect() as db:
        cursor = await db.execute(
            "INSERT INTO irk_keys (label, irk_hex) VALUES (?, ?)",
            (label, irk_hex),
        )
        await db.commit()
        return cursor.lastrowid


async def delete_irk_key(irk_id: int) -> None:
    async with _connect() as db:
        await db.execute("DELETE FROM irk_keys WHERE id = ?", (irk_id,))
        await db.commit()


async def resolve_irk_identity(mac: str) -> Optional[int]:
    """Try to resolve a randomized MAC against every configured IRK. On a
    match, returns the id of the identity named "IRK: <label>" (creating it
    if this is the first MAC that key has ever resolved) -- a cryptographic
    match is strictly stronger evidence than the advertised-name heuristic
    in upsert_device's auto-attach path, so callers should prefer this over
    (and let it override) a name-based identity_id when both are available.

    Returns None immediately, with no DB work, if no IRKs are configured or
    this MAC isn't a Resolvable Private Address in the first place."""
    if not _is_randomized_mac(mac):
        return None

    keys = await get_irk_keys()
    if not keys:
        return None

    irk_pairs = []
    for k in keys:
        try:
            irk_pairs.append((k["label"], rpa.parse_irk_hex(k["irk_hex"])))
        except ValueError:
            continue

    label = rpa.resolve_against_keys(mac, irk_pairs)
    if label is None:
        return None

    identity_name = f"IRK: {label}"
    async with _connect() as db:
        async with db.execute(
            "SELECT id FROM identities WHERE name = ? COLLATE NOCASE", (identity_name,)
        ) as cursor:
            row = await cursor.fetchone()
        if row:
            return row[0]
        cursor = await db.execute(
            "INSERT INTO identities (name) VALUES (?)", (identity_name,)
        )
        await db.commit()
        return cursor.lastrowid


async def get_wigle_credentials() -> Optional[tuple[str, str]]:
    """Returns (api_name, api_token) if WiGLE lookup is configured, else None.

    Stored via the generic settings key/value table rather than the
    Settings dataclass so the credential never has to round-trip through
    the general /api/settings GET response -- a dedicated masked endpoint
    handles display instead (see api_get_wigle_settings)."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT key, value FROM settings WHERE key IN ('wigle_api_name', 'wigle_api_token')"
        ) as cursor:
            rows = await cursor.fetchall()
    values = {row["key"]: row["value"] for row in rows}
    api_name = values.get("wigle_api_name")
    api_token = values.get("wigle_api_token")
    if not api_name or not api_token:
        return None
    return (api_name, api_token)


async def set_wigle_credentials(api_name: str, api_token: str) -> None:
    async with _connect() as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('wigle_api_name', ?)",
            (api_name,),
        )
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('wigle_api_token', ?)",
            (api_token,),
        )
        await db.commit()


async def clear_wigle_credentials() -> None:
    async with _connect() as db:
        await db.execute("DELETE FROM settings WHERE key IN ('wigle_api_name', 'wigle_api_token')")
        await db.commit()


async def get_fastpair_settings() -> bool:
    """Whether Fast Pair anti-spoof verification is enabled in Scan Unit.

    Stored via the generic settings table (same pattern as other toggles).
    There is no API key here -- Google doesn't publish a self-service
    lookup API for Anti-Spoofing Public Keys, so verification only works
    for Model IDs added by hand to the local key file (see fastpair.py)."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT value FROM settings WHERE key = 'fastpair_enabled'"
        ) as cursor:
            row = await cursor.fetchone()
    return bool(row and row["value"] == "1")


async def set_fastpair_settings(enabled: bool) -> None:
    async with _connect() as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('fastpair_enabled', ?)",
            ("1" if enabled else "0",),
        )
        await db.commit()


async def get_wigle_cache_entry(mac: str) -> Optional[dict]:
    """None means this MAC has never been checked against WiGLE. A dict
    (possibly with vendor=None) means it has -- callers should not query
    WiGLE again for it, to conserve the free-tier daily quota."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT vendor FROM wigle_lookup_cache WHERE mac = ?", (mac,)
        ) as cursor:
            row = await cursor.fetchone()
    return {"vendor": row["vendor"]} if row else None


async def set_wigle_cache_entry(mac: str, vendor: Optional[str]) -> None:
    async with _connect() as db:
        await db.execute(
            "INSERT OR REPLACE INTO wigle_lookup_cache (mac, vendor, checked_at) "
            "VALUES (?, ?, CURRENT_TIMESTAMP)",
            (mac, vendor),
        )
        await db.commit()


async def get_watched_devices() -> list[Device]:
    """Get all watched (devices of interest)."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM devices WHERE watched = 1 ORDER BY last_seen DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [_parse_device_row(row) for row in rows]


async def get_rssi_history(mac: str, days: int = 7) -> list[dict]:
    """Get RSSI history for a device for charting."""
    async with _connect() as db:
        async with db.execute(
            """
            SELECT timestamp, rssi
            FROM sightings
            WHERE mac = ? AND rssi IS NOT NULL AND timestamp > datetime('now', ?)
            ORDER BY timestamp ASC
            """,
            (mac, f"-{days} days")
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {"timestamp": row[0], "rssi": row[1]}
                for row in rows
            ]


# ============================================================================
# Dwell Time Analysis
# ============================================================================

async def get_dwell_time(mac: str, days: int = 30, gap_minutes: int = 15) -> dict:
    """Calculate dwell time statistics for a device.

    Dwell time is calculated as continuous presence periods, where gaps
    larger than gap_minutes start a new session.

    Returns:
        dict with total_minutes, session_count, avg_session_minutes,
        longest_session_minutes, sessions list
    """
    async with _connect() as db:
        async with db.execute(
            """
            SELECT timestamp FROM sightings
            WHERE mac = ? AND timestamp > datetime('now', ?)
            ORDER BY timestamp ASC
            """,
            (mac, f"-{days} days")
        ) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        return {
            "total_minutes": 0,
            "session_count": 0,
            "avg_session_minutes": 0,
            "longest_session_minutes": 0,
            "sessions": []
        }

    # Parse timestamps and calculate sessions
    timestamps = [datetime.fromisoformat(row[0]) for row in rows]
    gap_threshold = gap_minutes * 60  # Convert to seconds

    sessions = []
    session_start = timestamps[0]
    session_end = timestamps[0]

    for i in range(1, len(timestamps)):
        gap = (timestamps[i] - session_end).total_seconds()
        if gap > gap_threshold:
            # End current session, start new one
            duration = (session_end - session_start).total_seconds() / 60
            sessions.append({
                "start": session_start.isoformat() + "Z",
                "end": session_end.isoformat() + "Z",
                "duration_minutes": round(duration, 1)
            })
            session_start = timestamps[i]
        session_end = timestamps[i]

    # Don't forget the last session
    duration = (session_end - session_start).total_seconds() / 60
    sessions.append({
        "start": session_start.isoformat() + "Z",
        "end": session_end.isoformat() + "Z",
        "duration_minutes": round(duration, 1)
    })

    total_minutes = sum(s["duration_minutes"] for s in sessions)
    longest = max(s["duration_minutes"] for s in sessions) if sessions else 0

    return {
        "total_minutes": round(total_minutes, 1),
        "session_count": len(sessions),
        "avg_session_minutes": round(total_minutes / len(sessions), 1) if sessions else 0,
        "longest_session_minutes": round(longest, 1),
        "sessions": sessions[-10:]  # Return last 10 sessions
    }


# ============================================================================
# Device Correlation Analysis
# ============================================================================

def _sessions_from_timestamps(timestamps: list[datetime], gap_seconds: float) -> list[tuple[datetime, datetime]]:
    """Collapse a sorted list of sighting timestamps into presence sessions.

    A gap larger than ``gap_seconds`` between consecutive sightings ends the
    current session and starts a new one. Returns a list of (start, end)
    tuples — start is an "arrival" (came online), end is a "departure"
    (went offline).
    """
    if not timestamps:
        return []

    sessions: list[tuple[datetime, datetime]] = []
    start = end = timestamps[0]
    for ts in timestamps[1:]:
        if (ts - end).total_seconds() > gap_seconds:
            sessions.append((start, end))
            start = ts
        end = ts
    sessions.append((start, end))
    return sessions


def _count_aligned_events(
    target_events: list[datetime],
    candidate_events: list[datetime],
    window_seconds: float,
) -> int:
    """Count target events that have a candidate event within ``window_seconds``.

    Both lists must be sorted ascending. Each target event contributes at most
    one match, so the result is in ``[0, len(target_events)]``.
    """
    if not target_events or not candidate_events:
        return 0

    matched = 0
    for event in target_events:
        idx = bisect.bisect_left(candidate_events, event)
        # Nearest candidate event is either at idx or idx-1.
        nearest = None
        if idx < len(candidate_events):
            nearest = (candidate_events[idx] - event).total_seconds()
        if idx > 0:
            prev = (event - candidate_events[idx - 1]).total_seconds()
            nearest = prev if nearest is None else min(nearest, prev)
        if nearest is not None and nearest <= window_seconds:
            matched += 1
    return matched


async def get_correlated_devices(
    mac: str,
    days: int = 30,
    window_minutes: int = 5,
    gap_minutes: int = 15,
    edge_minutes: Optional[int] = None,
) -> list[dict]:
    """Find devices that share presence patterns with the target device.

    Two complementary signals are combined, so this surfaces devices that may
    belong to the same person or group:

    * **Co-occurrence** — how often the two devices are seen at the same time
      (within ``window_minutes``).
    * **Transition sync** — how often they come online and go offline around
      the same time. Sightings are collapsed into presence sessions (a gap
      longer than ``gap_minutes`` starts a new session); a candidate's
      session arrivals/departures are matched against the target's within
      ``edge_minutes``. This distinguishes devices that genuinely arrive and
      leave together from those that merely happen to be around a lot.

    Args:
        mac: Target device MAC address
        days: Number of days to analyze
        window_minutes: Time window for co-occurrence (default 5 minutes)
        gap_minutes: Idle gap that ends a presence session (default 15 minutes)
        edge_minutes: Tolerance for matching arrivals/departures
            (defaults to ``window_minutes``)

    Returns:
        List of correlated devices, each with a combined ``correlation_score``
        plus the ``cooccurrence_score`` and ``transition_score`` components and
        the number of synced arrivals/departures.
    """
    if edge_minutes is None:
        edge_minutes = window_minutes
    edge_seconds = edge_minutes * 60
    gap_seconds = gap_minutes * 60

    async with _connect() as db:
        db.row_factory = aiosqlite.Row

        # Get all sightings of the target device (ordered, for session building).
        async with db.execute(
            """
            SELECT timestamp FROM sightings
            WHERE mac = ? AND timestamp > datetime('now', ?)
            ORDER BY timestamp ASC
            """,
            (mac, f"-{days} days")
        ) as cursor:
            target_rows = await cursor.fetchall()

        if not target_rows:
            return []

        target_count = len(target_rows)
        target_ts = [datetime.fromisoformat(row[0]) for row in target_rows]
        target_sessions = _sessions_from_timestamps(target_ts, gap_seconds)
        target_arrivals = [s[0] for s in target_sessions]
        target_departures = [s[1] for s in target_sessions]
        target_edge_count = len(target_arrivals) + len(target_departures)

        # Candidate pool: devices co-occurring with the target. We pull a wider
        # pool than we return so transition sync can re-rank the results.
        #
        # Each window bound is computed from s1 with datetime() and rewritten to
        # the 'T'-separated form that timestamps are stored in, so the bare,
        # indexed s2.timestamp can be range-compared as a raw string. Wrapping
        # the column itself in datetime() (the obvious way to normalize) forces a
        # full scan of the sightings table per target sighting; seeking the index
        # instead turns a ~30s query into single-digit milliseconds on a large
        # database. datetime() truncates to whole seconds, so the upper bound is
        # the next second (exclusive) to keep the boundary second inclusive,
        # exactly matching the previous datetime()-on-both-sides comparison.
        async with db.execute(
            """
            SELECT
                s2.mac,
                d.vendor,
                d.friendly_name,
                d.device_type,
                COUNT(*) as co_occurrences,
                d.total_sightings
            FROM sightings s1
            JOIN sightings s2 ON s2.mac != s1.mac
                AND s2.timestamp >= replace(datetime(s1.timestamp, ?), ' ', 'T')
                AND s2.timestamp <  replace(datetime(s1.timestamp, ?, '+1 second'), ' ', 'T')
            JOIN devices d ON d.mac = s2.mac
            WHERE s1.mac = ?
                AND s1.timestamp > datetime('now', ?)
                AND d.ignored = 0
            GROUP BY s2.mac
            HAVING co_occurrences >= 2
            ORDER BY co_occurrences DESC
            LIMIT 50
            """,
            (f"-{window_minutes} minutes", f"+{window_minutes} minutes", mac, f"-{days} days")
        ) as cursor:
            rows = await cursor.fetchall()

        if not rows:
            return []

        # Fetch every candidate's sightings in one pass and group by MAC so we
        # can build their presence sessions in Python.
        candidate_macs = [row["mac"] for row in rows]
        placeholders = ", ".join("?" for _ in candidate_macs)
        async with db.execute(
            f"""
            SELECT mac, timestamp FROM sightings
            WHERE mac IN ({placeholders}) AND timestamp > datetime('now', ?)
            ORDER BY mac ASC, timestamp ASC
            """,
            (*candidate_macs, f"-{days} days")
        ) as cursor:
            sighting_rows = await cursor.fetchall()

        sightings_by_mac: dict[str, list[datetime]] = {}
        for row in sighting_rows:
            sightings_by_mac.setdefault(row["mac"], []).append(
                datetime.fromisoformat(row["timestamp"])
            )

        results = []
        for row in rows:
            # Co-occurrence: ratio of co-sightings to the target's sightings.
            cooccurrence_score = min(100, round((row["co_occurrences"] / target_count) * 100))

            # Transition sync: how many of the target's arrivals/departures the
            # candidate matches with one of its own.
            cand_sessions = _sessions_from_timestamps(
                sightings_by_mac.get(row["mac"], []), gap_seconds
            )
            cand_arrivals = [s[0] for s in cand_sessions]
            cand_departures = [s[1] for s in cand_sessions]
            synced_arrivals = _count_aligned_events(target_arrivals, cand_arrivals, edge_seconds)
            synced_departures = _count_aligned_events(target_departures, cand_departures, edge_seconds)
            transition_score = (
                round(((synced_arrivals + synced_departures) / target_edge_count) * 100)
                if target_edge_count else 0
            )

            # Combined score weights co-presence and synchronized transitions
            # equally so co-travellers outrank devices that are merely always around.
            correlation = round(0.5 * cooccurrence_score + 0.5 * transition_score)

            results.append({
                "mac": row["mac"],
                "vendor": row["vendor"],
                "friendly_name": row["friendly_name"],
                "device_type": row["device_type"],
                "co_occurrences": row["co_occurrences"],
                "total_sightings": row["total_sightings"],
                "correlation_score": correlation,
                "cooccurrence_score": cooccurrence_score,
                "transition_score": transition_score,
                "synced_arrivals": synced_arrivals,
                "synced_departures": synced_departures,
            })

        results.sort(key=lambda r: (r["correlation_score"], r["co_occurrences"]), reverse=True)
        return results[:20]


def _median_ping_gap(timestamps: list[datetime]) -> Optional[float]:
    """Median seconds between consecutive sightings (a device's ping cadence).

    The median shrugs off the occasional long absence between presence
    sessions, so it reflects the typical advertising interval.
    """
    if len(timestamps) < 2:
        return None
    gaps = [
        (timestamps[i] - timestamps[i - 1]).total_seconds()
        for i in range(1, len(timestamps))
    ]
    gaps = [g for g in gaps if g > 0]
    return statistics.median(gaps) if gaps else None


async def get_rotation_candidates(
    mac: str,
    days: int = 7,
    rssi_tolerance: int = 6,
    overlap_window_seconds: int = 30,
    max_overlap_ratio: float = 0.1,
    max_handoff_seconds: int = 1800,
    min_sightings: int = 5,
) -> dict:
    """Find devices that are likely the *same physical device* as ``mac``.

    Modern devices rotate their Bluetooth MAC for privacy, so one phone shows
    up as many short-lived randomized identifiers. Two identifiers are flagged
    as likely the same device when they:

    * are both **randomized** (locally-administered) MACs,
    * **coexist in the same overall period** but are essentially never seen at
      the same instant — the old identity goes quiet as the new one appears
      (a handoff rather than two co-present devices),
    * sit at a **similar signal strength** (mean RSSI within ``rssi_tolerance``
      dB), and
    * **ping at a similar cadence**.

    This is a probabilistic heuristic, not proof — RSSI is noisy and devices at
    similar distances can coincide. Returns a dict with the target's own signal
    profile and a confidence-ranked list of candidates.
    """
    empty = {"target": None, "candidates": []}

    async with _connect() as db:
        db.row_factory = aiosqlite.Row

        # The advertised name is a strong same-device signal: some devices keep
        # a constant local name (AirPods, named accessories) while rotating MAC.
        async with db.execute(
            "SELECT friendly_name FROM devices WHERE mac = ?", (mac,)
        ) as cursor:
            name_row = await cursor.fetchone()
        target_name = ((name_row["friendly_name"] if name_row else "") or "").strip()

        async with db.execute(
            """
            SELECT timestamp, rssi FROM sightings
            WHERE mac = ? AND rssi IS NOT NULL AND timestamp > datetime('now', ?)
            ORDER BY timestamp ASC
            """,
            (mac, f"-{days} days")
        ) as cursor:
            target_rows = await cursor.fetchall()

        if len(target_rows) < min_sightings:
            return empty

        t_ts = [datetime.fromisoformat(r["timestamp"]) for r in target_rows]
        t_rssi = [r["rssi"] for r in target_rows]
        t_mean = statistics.fmean(t_rssi)
        t_std = statistics.pstdev(t_rssi) if len(t_rssi) > 1 else 0.0
        t_gap = _median_ping_gap(t_ts)
        t_first, t_last = t_ts[0], t_ts[-1]

        # Candidate pool: randomized, non-ignored devices at a comparable mean
        # RSSI, with enough sightings to be meaningful. Filtered in SQL to keep
        # the per-candidate Python work bounded. A device that shares the
        # target's exact advertised name is admitted even when its RSSI falls
        # outside the tolerance — the name is reason enough to evaluate it, and
        # the handoff/non-overlap checks below still gate it on rotation shape.
        randomized = _randomized_mac_sql("d.mac")
        params = [mac, f"-{days} days", min_sightings, t_mean, rssi_tolerance]
        name_having = ""
        if target_name:
            name_having = " OR lower(d.friendly_name) = lower(?)"
            params.append(target_name)
        async with db.execute(
            f"""
            SELECT s.mac AS mac, AVG(s.rssi) AS mean_rssi, COUNT(*) AS cnt
            FROM sightings s
            JOIN devices d ON d.mac = s.mac
            WHERE s.mac != ?
              AND s.rssi IS NOT NULL
              AND s.timestamp > datetime('now', ?)
              AND d.ignored = 0
              AND {randomized}
            GROUP BY s.mac
            HAVING cnt >= ? AND (ABS(AVG(s.rssi) - ?) <= ?{name_having})
            """,
            params
        ) as cursor:
            cand_rows = await cursor.fetchall()

        if not cand_rows:
            return {"target": _rotation_target_profile(t_mean, t_std, t_gap, len(t_ts)), "candidates": []}

        cand_macs = [r["mac"] for r in cand_rows]
        placeholders = ", ".join("?" for _ in cand_macs)
        async with db.execute(
            f"""
            SELECT mac, timestamp, rssi FROM sightings
            WHERE mac IN ({placeholders}) AND rssi IS NOT NULL
              AND timestamp > datetime('now', ?)
            ORDER BY mac ASC, timestamp ASC
            """,
            (*cand_macs, f"-{days} days")
        ) as cursor:
            sighting_rows = await cursor.fetchall()

        async with db.execute(
            f"SELECT mac, vendor, friendly_name, device_type FROM devices WHERE mac IN ({placeholders})",
            cand_macs
        ) as cursor:
            meta = {r["mac"]: r for r in await cursor.fetchall()}

    by_mac: dict[str, list] = {}
    for r in sighting_rows:
        by_mac.setdefault(r["mac"], []).append(
            (datetime.fromisoformat(r["timestamp"]), r["rssi"])
        )

    results = []
    for cmac, pts in by_mac.items():
        if len(pts) < min_sightings:
            continue
        c_ts = [p[0] for p in pts]
        c_rssi = [p[1] for p in pts]
        c_first, c_last = c_ts[0], c_ts[-1]

        # Must belong to the same continuous presence: either the active windows
        # overlap (interleaved rotation) or they sit back-to-back within a
        # handoff gap (old identity goes quiet, new one appears shortly after).
        if c_last < t_first:
            handoff_gap = (t_first - c_last).total_seconds()
        elif t_last < c_first:
            handoff_gap = (c_first - t_last).total_seconds()
        else:
            handoff_gap = 0.0
        if handoff_gap > max_handoff_seconds:
            continue

        # ...but must NOT ping simultaneously: the same physical device only
        # broadcasts one random MAC at a time.
        simultaneous = _count_aligned_events(c_ts, t_ts, overlap_window_seconds)
        overlap_ratio = simultaneous / min(len(c_ts), len(t_ts))
        if overlap_ratio > max_overlap_ratio:
            continue

        c_mean = statistics.fmean(c_rssi)
        c_std = statistics.pstdev(c_rssi) if len(c_rssi) > 1 else 0.0
        c_gap = _median_ping_gap(c_ts)

        rssi_delta = abs(c_mean - t_mean)
        rssi_sim = 1 - min(1.0, rssi_delta / rssi_tolerance)
        cadence_sim = (min(t_gap, c_gap) / max(t_gap, c_gap)) if (t_gap and c_gap) else 0.0
        separation = 1 - overlap_ratio
        base = 0.4 * rssi_sim + 0.3 * separation + 0.3 * cadence_sim

        m = meta[cmac]
        cand_name = ((m["friendly_name"] or "")).strip()
        name_match = bool(target_name) and cand_name.lower() == target_name.lower()
        # A shared advertised name floors confidence at 60 and scales the signal
        # heuristics into the top band; without it, the heuristics stand alone.
        confidence = round(100 * (0.6 + 0.4 * base)) if name_match else round(100 * base)

        results.append({
            "mac": cmac,
            "vendor": m["vendor"],
            "friendly_name": m["friendly_name"],
            "device_type": m["device_type"],
            "name_match": name_match,
            "confidence": confidence,
            "mean_rssi": round(c_mean, 1),
            "rssi_delta": round(rssi_delta, 1),
            "rssi_stddev": round(c_std, 1),
            "ping_interval_seconds": round(c_gap) if c_gap else None,
            "overlap_ratio": round(overlap_ratio, 3),
            "handoff_seconds": round(handoff_gap),
            "sightings": len(c_ts),
            "first_seen": c_first.isoformat() + "Z",
            "last_seen": c_last.isoformat() + "Z",
        })

    results.sort(key=lambda x: x["confidence"], reverse=True)
    return {
        "target": _rotation_target_profile(t_mean, t_std, t_gap, len(t_ts)),
        "candidates": results[:10],
    }


def _rotation_target_profile(mean: float, std: float, gap: Optional[float], count: int) -> dict:
    """Signal profile for the device being inspected (shown for context)."""
    return {
        "mean_rssi": round(mean, 1),
        "rssi_stddev": round(std, 1),
        "ping_interval_seconds": round(gap) if gap else None,
        "sightings": count,
    }


# ============================================================================
# Name-based Grouping
# ============================================================================

async def get_name_groups(
    min_devices: int = 2,
    include_ignored: bool = False,
) -> list[dict]:
    """Group devices that advertise the same name across different MAC addresses.

    Apple-style MAC randomization makes a single physical device surface as many
    rows that share an identical advertised name. This collapses devices by their
    exact (case-insensitive) ``friendly_name`` and returns only the names carried
    by more than one MAC, so duplicates from rotation are visible at a glance.

    Randomized MACs are intentionally included here — they are the whole point of
    the view. Each group reports how many of its members are randomized so a
    genuine rotating device (mostly randomized) reads differently from several
    distinct devices that merely happen to share a generic name.
    """
    conditions = ["friendly_name IS NOT NULL", "TRIM(friendly_name) != ''"]
    if not include_ignored:
        conditions.append("ignored = 0")
    where_clause = " AND ".join(conditions)
    randomized_count_sql = _randomized_mac_sql("mac")
    safe_min = max(2, min_devices)

    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            f"""
            SELECT
                MIN(friendly_name) AS name,
                COUNT(*) AS device_count,
                SUM(CASE WHEN {randomized_count_sql} THEN 1 ELSE 0 END) AS randomized_count,
                SUM(COALESCE(total_sightings, 0)) AS total_sightings,
                MIN(first_seen) AS first_seen,
                MAX(last_seen) AS last_seen,
                GROUP_CONCAT(mac, '||') AS macs,
                GROUP_CONCAT(COALESCE(vendor, ''), '||') AS vendors,
                GROUP_CONCAT(COALESCE(device_type, ''), '||') AS device_types
            FROM devices
            WHERE {where_clause}
            GROUP BY lower(friendly_name)
            HAVING device_count >= ?
            ORDER BY device_count DESC, last_seen DESC
            """,
            (safe_min,),
        ) as cursor:
            rows = await cursor.fetchall()

    results = []
    for row in rows:
        macs = [m for m in (row["macs"] or "").split("||") if m]
        vendors = [v for v in (row["vendors"] or "").split("||") if v]
        types = [t for t in (row["device_types"] or "").split("||") if t]
        results.append({
            "name": row["name"],
            "device_count": int(row["device_count"] or 0),
            "randomized_count": int(row["randomized_count"] or 0),
            "total_sightings": int(row["total_sightings"] or 0),
            "first_seen": (row["first_seen"] + "Z") if row["first_seen"] else None,
            "last_seen": (row["last_seen"] + "Z") if row["last_seen"] else None,
            "macs": macs,
            "vendor": vendors[0] if vendors else None,
            "device_type": types[0] if types else None,
        })
    return results


# ============================================================================
# Proximity Zone Helpers
# ============================================================================

def rssi_to_proximity_zone(rssi: int) -> str:
    """Convert RSSI value to a proximity zone label.

    RSSI ranges are approximate and vary by device/environment:
    - Immediate: Very close (< 1m)
    - Near: Close proximity (1-3m)
    - Far: Same room/area (3-10m)
    - Remote: Detectable but far (> 10m)
    """
    if rssi is None:
        return "unknown"
    if rssi >= -50:
        return "immediate"
    elif rssi >= -65:
        return "near"
    elif rssi >= -80:
        return "far"
    else:
        return "remote"


async def get_proximity_stats(mac: str, days: int = 7) -> dict:
    """Get proximity zone statistics for a device.

    Returns distribution of sightings across proximity zones.
    """
    async with _connect() as db:
        async with db.execute(
            """
            SELECT rssi FROM sightings
            WHERE mac = ? AND rssi IS NOT NULL AND timestamp > datetime('now', ?)
            """,
            (mac, f"-{days} days")
        ) as cursor:
            rows = await cursor.fetchall()

    zones = {"immediate": 0, "near": 0, "far": 0, "remote": 0}
    for row in rows:
        zone = rssi_to_proximity_zone(row[0])
        if zone in zones:
            zones[zone] += 1

    total = sum(zones.values())
    if total > 0:
        zones_pct = {k: round(v / total * 100, 1) for k, v in zones.items()}
    else:
        zones_pct = {k: 0 for k in zones}

    # Determine dominant zone
    dominant = max(zones.items(), key=lambda x: x[1])[0] if total > 0 else "unknown"

    return {
        "zones": zones,
        "zones_percent": zones_pct,
        "total_readings": total,
        "dominant_zone": dominant
    }
