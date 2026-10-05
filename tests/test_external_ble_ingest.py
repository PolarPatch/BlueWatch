"""External BLE receiver contract tests."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from aiohttp import web

from bluewatch import db
from bluewatch.ingest import ExternalBleIngestion, normalize_observation


def observation():
    return {
        "address": "02:11:22:33:44:55",
        "name": "Test sensor",
        "rssi": -67,
        "observed_at": datetime.now(UTC).isoformat(),
        "source": "proxy-one",
        "connectable": False,
        "service_uuids": ["0000181a-0000-1000-8000-00805f9b34fb"],
        "manufacturer_data": {},
        "service_data": {},
        "appearance": None,
    }


def batch(item=None):
    return {
        "schema_version": 1,
        "producer_id": "test-producer",
        "batch_id": str(uuid4()),
        "sent_at": datetime.now(UTC).isoformat(),
        "observations": [item or observation()],
    }


@pytest.mark.parametrize(
    "patch",
    [
        {"rssi": True},
        {"rssi": -200},
        {"address": "../invalid"},
        {"service_uuids": [1]},
        {"service_uuids": ["invalid"]},
        {"manufacturer_data": {"1": "!"}},
        {"manufacturer_data": {"70000": "AA=="}},
        {"connectable": "true"},
        {"observed_at": "2020-01-01T00:00:00Z"},
        {"observed_at": "2026-10-05"},
    ],
)
def test_invalid_observation(patch):
    with pytest.raises((ValueError, TypeError)):
        normalize_observation(observation() | patch)


def test_accumulated_metadata_is_bounded():
    item = observation() | {
        "manufacturer_data": {str(company): "AA==" for company in range(96)}
    }
    result = normalize_observation(item)
    assert len(result["manufacturer_data"]) == 32
    assert set(result["manufacturer_data"]) == set(range(64, 96))


@pytest.mark.asyncio
async def test_v1_ingest_is_authenticated_deduplicated_and_timestamped(
    aiohttp_client, monkeypatch, tmp_path
):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "receiver.db")
    await db.init_db()
    monkeypatch.setenv("BLUEWATCH_INGEST_TOKEN", "a" * 48)
    server = AsyncMock()
    receiver = ExternalBleIngestion(server)
    app = web.Application()
    app.router.add_post("/api/v1/observations/ble", receiver.ingest)
    app.router.add_get("/api/v1/observations/ble/capabilities", receiver.capabilities)
    app.router.add_get("/api/external-ble/status", receiver.status)
    app.router.add_post("/api/external-ble/enabled", receiver.set_enabled)
    client = await aiohttp_client(app)
    payload = batch()

    for headers in (
        {},
        {"Authorization": "Bearer wrong"},
        {"Authorization": "Basic x"},
    ):
        assert (
            await client.post("/api/v1/observations/ble", json=payload, headers=headers)
        ).status == 401

    headers = {"Authorization": "Bearer " + "a" * 48}
    capabilities = await client.get(
        "/api/v1/observations/ble/capabilities", headers=headers
    )
    assert capabilities.status == 200
    assert (await capabilities.json())["schema_versions"] == [1]

    response = await client.post(
        "/api/v1/observations/ble", json=payload, headers=headers
    )
    assert response.status == 200
    assert (await response.json())["accepted"] == 1
    response = await client.post(
        "/api/v1/observations/ble", json=payload, headers=headers
    )
    assert (await response.json())["deduplicated"] == 1
    assert server.broadcast_sighting.await_count == 1
    assert server._notifications.on_device_seen.await_count == 1

    item = payload["observations"][0]
    device = await db.get_device(item["address"])
    assert device.total_sightings == 1
    latest = device.last_seen
    older = observation() | {
        "observed_at": (datetime.now(UTC) - timedelta(seconds=20)).isoformat()
    }
    await db.upsert_device(**normalize_observation(older))
    assert (await db.get_device(item["address"])).last_seen == latest

    async with db._connect() as connection:
        rows = await (
            await connection.execute("SELECT source FROM sightings ORDER BY id")
        ).fetchall()
    assert rows[0][0] == item["source"]

    assert (
        await client.post("/api/external-ble/enabled", json={"enabled": False})
    ).status == 200
    assert (
        await client.post("/api/v1/observations/ble", json=batch(), headers=headers)
    ).status == 503
    assert (
        await client.post("/api/external-ble/enabled", json={"enabled": "false"})
    ).status == 400


@pytest.mark.asyncio
async def test_legacy_route_remains_compatible(aiohttp_client, monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "legacy.db")
    await db.init_db()
    monkeypatch.setenv("BLUEWATCH_INGEST_TOKEN", "b" * 48)
    receiver = ExternalBleIngestion(AsyncMock())
    app = web.Application()
    app.router.add_post("/api/ingest/ble", receiver.ingest)
    client = await aiohttp_client(app)
    payload = {
        "scanner": "legacy-bridge",
        "sent_at": datetime.now(UTC).isoformat(),
        "observations": [observation()],
    }
    response = await client.post(
        "/api/ingest/ble",
        json=payload,
        headers={"Authorization": "Bearer " + "b" * 48},
    )
    assert response.status == 200
    assert (await response.json())["accepted"] == 1
