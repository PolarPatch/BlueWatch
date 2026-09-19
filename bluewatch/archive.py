"""Automatic export of old observations to CSV, followed by removal from the
database, so the live database stays small and fast.

Old rows from the `sightings` table are written to one CSV file per day in
`<data dir>/exports/` and only deleted once the file is complete and its row
count matches the database. The small `hourly_seen` rollup is kept, so the
statistics graphs still cover the exported period.
"""

import asyncio
import csv
import json
import logging
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import aiosqlite

from . import db
from .config import DATA_DIR

logger = logging.getLogger(__name__)

EXPORT_DIR = Path(DATA_DIR) / "exports"
FILE_RE = re.compile(r"^sightings_\d{4}-\d{2}-\d{2}(?:_\d+)?\.csv$")
MIN_FREE_BYTES = 200 * 1024 * 1024  # don't start an export with less free space
MAX_DAYS_PER_RUN = 14
CSV_HEADER = ["timestamp", "mac", "rssi", "vendor", "name", "type"]

_run_lock = asyncio.Lock()
_running = False


def is_running() -> bool:
    return _running


def _next_free_name(day: str) -> Path:
    path = EXPORT_DIR / f"sightings_{day}.csv"
    n = 2
    while path.exists():
        path = EXPORT_DIR / f"sightings_{day}_{n}.csv"
        n += 1
    return path


def list_files() -> list[dict]:
    if not EXPORT_DIR.is_dir():
        return []
    out = []
    for p in sorted(EXPORT_DIR.iterdir(), reverse=True):
        if FILE_RE.match(p.name):
            st = p.stat()
            out.append({
                "name": p.name,
                "size": st.st_size,
                "modified": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
            })
    return out


def file_path(name: str) -> Optional[Path]:
    """Path of an exported file, only for names this module produced."""
    if not FILE_RE.match(name):
        return None
    p = EXPORT_DIR / name
    return p if p.is_file() else None


def free_bytes() -> int:
    try:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        return shutil.disk_usage(EXPORT_DIR).free
    except OSError:
        return 0


async def _export_day(day: str) -> tuple[int, Path]:
    """Write one day of sightings to CSV and delete them from the database.
    Returns (rows exported, file). Raises if the file doesn't match the DB."""
    start, end = day, day + "~"
    final = _next_free_name(day)
    tmp = final.with_suffix(".csv.part")
    rows = 0
    async with db._connect() as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT COUNT(*) FROM sightings WHERE timestamp >= ? AND timestamp < ?", (start, end)
        ) as cursor:
            expected = (await cursor.fetchone())[0]
        with open(tmp, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(CSV_HEADER)
            async with conn.execute(
                "SELECT s.timestamp, s.mac, s.rssi, d.vendor, d.friendly_name, "
                "COALESCE(d.device_type, d.auto_type) AS type "
                "FROM sightings s LEFT JOIN devices d ON d.mac = s.mac "
                "WHERE s.timestamp >= ? AND s.timestamp < ? ORDER BY s.timestamp",
                (start, end),
            ) as cursor:
                while True:
                    batch = await cursor.fetchmany(5000)
                    if not batch:
                        break
                    writer.writerows(
                        [(r["timestamp"], r["mac"], r["rssi"], r["vendor"], r["friendly_name"], r["type"]) for r in batch]
                    )
                    rows += len(batch)
            fh.flush()
    if rows != expected:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"{day}: wrote {rows} rows but the database has {expected}")
    tmp.rename(final)

    # The file is complete: now remove those rows, in small chunks so the
    # scanner's writes are never blocked for long.
    while True:
        async with db._connect() as conn:
            cursor = await conn.execute(
                "DELETE FROM sightings WHERE id IN ("
                "SELECT id FROM sightings WHERE timestamp >= ? AND timestamp < ? LIMIT 20000)",
                (start, end),
            )
            await conn.commit()
            if cursor.rowcount <= 0:
                break
        await asyncio.sleep(0.2)
    return rows, final


async def run_export(days: int) -> dict:
    """Export and remove every day of sightings older than `days` days."""
    global _running
    if _run_lock.locked():
        return {"ok": False, "error": "An export is already running"}
    async with _run_lock:
        _running = True
        try:
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            if free_bytes() < MIN_FREE_BYTES:
                result = {"ok": False, "error": "Not enough free disk space (need 200 MB)"}
            else:
                cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                async with db._connect() as conn:
                    async with conn.execute(
                        "SELECT DISTINCT substr(timestamp, 1, 10) FROM sightings "
                        "WHERE timestamp < ? ORDER BY 1",
                        (cutoff,),
                    ) as cursor:
                        pending = [r[0] for r in await cursor.fetchall()]
                exported, files, total_rows = [], [], 0
                for day in pending[:MAX_DAYS_PER_RUN]:
                    rows, path = await _export_day(day)
                    exported.append(day)
                    files.append(path.name)
                    total_rows += rows
                    logger.info(f"Exported {rows} sightings from {day} to {path.name}")
                result = {
                    "ok": True,
                    "days": len(exported),
                    "rows": total_rows,
                    "files": files,
                    "remaining_days": max(0, len(pending) - len(exported)),
                }
                if exported:
                    freed = await db.vacuum_if_fragmented()
                    if freed:
                        logger.info(f"Vacuumed database, reclaimed ~{freed} MB on disk")
        except Exception as e:
            logger.warning(f"Automatic export failed: {e}")
            result = {"ok": False, "error": str(e)}
        finally:
            _running = False
        result["finished"] = datetime.now().isoformat(timespec="seconds")
        await db.set_setting("auto_export_last_run", result["finished"])
        await db.set_setting("auto_export_last_result", json.dumps(result))
        return result
