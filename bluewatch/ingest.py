"""Authenticated, bounded ingestion of external BLE observations."""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import re
from datetime import UTC, datetime
from uuid import UUID

from aiohttp import web

from . import db

MAX_BODY = 262_144
MAX_BATCH = 100
MAX_METADATA_ENTRIES = 32
MAX_OBSERVATION_AGE = 120
MAX_FUTURE_SECONDS = 10
MAC = re.compile(r"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\Z")
logger = logging.getLogger(__name__)


def parse_timestamp(value: str) -> datetime:
    """Parse a recent, timezone-aware timestamp."""
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("timestamp")
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("timezone required")
    age = (datetime.now(UTC) - result).total_seconds()
    if not -MAX_FUTURE_SECONDS <= age <= MAX_OBSERVATION_AGE:
        raise ValueError("stale or future observation")
    return result


def normalize_observation(item: dict) -> dict:
    """Validate and decode one protocol observation."""
    if not isinstance(item, dict):
        raise TypeError("observation")
    address = item.get("address")
    if not isinstance(address, str) or not MAC.fullmatch(address):
        raise ValueError("address")
    rssi = item.get("rssi")
    if type(rssi) is not int or not -127 <= rssi <= 20:
        raise ValueError("rssi")
    source = item.get("source")
    if not isinstance(source, str) or not 1 <= len(source) <= 128:
        raise ValueError("source")
    name = item.get("name")
    if name is not None and (not isinstance(name, str) or len(name) > 248):
        raise ValueError("name")

    uuids = item.get("service_uuids", [])
    if (
        not isinstance(uuids, list)
        or len(uuids) > MAX_METADATA_ENTRIES
        or not all(isinstance(value, str) for value in uuids)
    ):
        raise ValueError("service UUIDs")
    uuids = [str(UUID(value)) for value in uuids]

    binary = {}
    for field in ("manufacturer_data", "service_data"):
        values = item.get(field, {})
        if not isinstance(values, dict):
            raise TypeError(f"{field} type")
        # HA can accumulate rotating metadata. Keep a bounded recent subset
        # instead of rejecting the identity and signal observation entirely.
        values = dict(list(values.items())[-MAX_METADATA_ENTRIES:])
        decoded = {}
        for key, value in values.items():
            if not isinstance(value, str) or len(value) > 2_200:
                raise ValueError("binary size")
            if field == "manufacturer_data":
                if (
                    not isinstance(key, str)
                    or not key.isdecimal()
                    or len(key) > 5
                    or not 0 <= int(key) <= 65_535
                ):
                    raise ValueError("company ID")
                key = int(key)
            else:
                key = str(UUID(key))
            raw = base64.b64decode(value, validate=True)
            if len(raw) > 1_650:
                raise ValueError("binary size")
            decoded[key] = raw
        binary[field] = decoded

    appearance = item.get("appearance")
    if appearance is not None and (
        type(appearance) is not int or not 0 <= appearance <= 65_535
    ):
        raise ValueError("appearance")
    if type(item.get("connectable")) is not bool:
        raise ValueError("connectable")

    observed = parse_timestamp(item.get("observed_at"))
    canonical = dict(
        item,
        address=address.upper(),
        observed_at=observed.astimezone(UTC).isoformat(),
    )
    ingest_key = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "mac": address.upper(),
        "friendly_name": name,
        "rssi": rssi,
        "service_uuids": uuids,
        "appearance": appearance,
        "observed_at": observed.astimezone().replace(tzinfo=None),
        "ingest_key": ingest_key,
        "ingest_source": source,
        **binary,
    }


class ExternalBleIngestion:
    """Receive observations without coupling BlueWatch to their producer."""

    def __init__(self, server):
        self.server = server
        configured_token = os.environ.get("BLUEWATCH_INGEST_TOKEN", "")
        self.token = configured_token if len(configured_token) >= 32 else ""
        if configured_token and not self.token:
            logger.error("BLUEWATCH_INGEST_TOKEN must contain at least 32 characters")
        self.lock = asyncio.Lock()
        self.stats = {
            "accepted": 0,
            "rejected": 0,
            "deduplicated": 0,
            "last_batch": None,
            "sources": [],
            "source_count": 0,
        }

    def _authenticate(self, request: web.Request) -> None:
        if not self.token:
            raise web.HTTPServiceUnavailable(
                text="External BLE ingestion not configured"
            )
        supplied = request.headers.get("Authorization", "")
        expected = "Bearer " + self.token
        if not hmac.compare_digest(supplied.encode(), expected.encode()):
            raise web.HTTPUnauthorized()

    async def capabilities(self, request: web.Request) -> web.Response:
        """Return receiver limits after authenticating the sender."""
        self._authenticate(request)
        return web.json_response(
            {
                "schema_versions": [1],
                "enabled": await db.get_external_ble_ingest_enabled(),
                "max_body_bytes": MAX_BODY,
                "max_batch_size": MAX_BATCH,
                "max_observation_age_seconds": MAX_OBSERVATION_AGE,
                "server_time": datetime.now(UTC).isoformat(),
            }
        )

    async def status(self, request: web.Request) -> web.Response:
        """Return receiver status to an authenticated dashboard session."""
        del request
        enabled = bool(self.token) and await db.get_external_ble_ingest_enabled()
        return web.json_response(
            {
                **self.stats,
                "enabled": enabled,
                "authentication": "configured" if self.token else "disabled",
            }
        )

    async def set_enabled(self, request: web.Request) -> web.Response:
        """Persist the dashboard kill switch."""
        try:
            payload = await request.json()
        except (ValueError, TypeError, json.JSONDecodeError):
            raise web.HTTPBadRequest(text="Invalid setting") from None
        if set(payload) != {"enabled"} or type(payload["enabled"]) is not bool:
            raise web.HTTPBadRequest(text="Invalid setting")
        await db.set_external_ble_ingest_enabled(payload["enabled"])
        return web.json_response(
            {
                "enabled": payload["enabled"] and bool(self.token),
                "authentication": "configured" if self.token else "disabled",
            }
        )

    async def ingest(self, request: web.Request) -> web.Response:
        """Validate and ingest a V1 or legacy batch."""
        self._authenticate(request)
        if not await db.get_external_ble_ingest_enabled():
            raise web.HTTPServiceUnavailable(text="External BLE ingestion disabled")
        if self.lock.locked():
            raise web.HTTPTooManyRequests()

        async with self.lock:
            raw = bytearray()
            try:
                async with asyncio.timeout(10):
                    async for chunk in request.content.iter_chunked(16_384):
                        raw.extend(chunk)
                        if len(raw) > MAX_BODY:
                            raise web.HTTPRequestEntityTooLarge(
                                max_size=MAX_BODY, actual_size=len(raw)
                            )
            except TimeoutError:
                raise web.HTTPRequestTimeout() from None

            try:
                payload = json.loads(raw)
                legacy = request.path == "/api/ingest/ble"
                if not isinstance(payload, dict):
                    raise TypeError("batch")
                if legacy:
                    producer_id = payload.get("scanner")
                    if not isinstance(producer_id, str) or not producer_id:
                        raise ValueError("scanner")
                else:
                    if payload.get("schema_version") != 1:
                        raise ValueError("schema version")
                    producer_id = payload.get("producer_id")
                    if (
                        not isinstance(producer_id, str)
                        or not 1 <= len(producer_id) <= 128
                    ):
                        raise ValueError("producer")
                    UUID(payload.get("batch_id"))
                parse_timestamp(payload.get("sent_at"))
                observations = payload["observations"]
                if (
                    not isinstance(observations, list)
                    or not 1 <= len(observations) <= MAX_BATCH
                ):
                    raise ValueError("batch size")
            except (ValueError, TypeError, KeyError, AttributeError):
                raise web.HTTPBadRequest(text="Invalid batch") from None

            counts = {"accepted": 0, "rejected": 0, "deduplicated": 0}
            sources = set()
            from .webapp.server import _device_to_json

            for item in observations:
                try:
                    normalized = normalize_observation(item)
                except (ValueError, TypeError, AttributeError, OverflowError) as error:
                    counts["rejected"] += 1
                    logger.warning(
                        "Rejected external BLE observation address=%s source=%s reason=%s",
                        item.get("address") if isinstance(item, dict) else None,
                        item.get("source") if isinstance(item, dict) else None,
                        error,
                    )
                    continue
                device, is_new = await db.upsert_device(**normalized)
                if device is None:
                    counts["deduplicated"] += 1
                    continue
                counts["accepted"] += 1
                sources.add(normalized["ingest_source"])
                try:
                    await self.server.broadcast_sighting(_device_to_json(device))
                    if self.server._notifications:
                        await self.server._notifications.on_device_seen(device, is_new)
                except Exception:
                    logger.exception("External BLE notification delivery failed")

            for key, value in counts.items():
                self.stats[key] += value
            self.stats.update(
                last_batch=datetime.now(UTC).isoformat(),
                sources=sorted(sources),
                source_count=len(sources),
            )
            return web.json_response(counts)
