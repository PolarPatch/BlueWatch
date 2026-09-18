"""BlueWatch daemon - continuous Bluetooth scanning service."""

import argparse
import asyncio
import json
import logging
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import aiohttp

from . import active_scan, db, wigle, __version__
from .classifier import is_randomized_mac
from .config import SCAN_INTERVAL, SOCKET_PATH, METRICS_PORT
from .scanner import BluetoothScanner, ScannedDevice, list_adapters
from .esp32_scanner import ESP32Scanner
from .web import WebServer
from .webapp.server import _device_to_json
from .notifications import NotificationManager

def _sd_notify(message: str) -> None:
    """Send a message to systemd over the $NOTIFY_SOCKET datagram socket
    (sd_notify, e.g. "WATCHDOG=1") -- a no-op outside systemd (no env
    var set) or on any error, so this is always safe to call. Talks to
    the socket directly rather than pulling in the `sdnotify` package,
    since the protocol is a single UDP-style datagram write."""
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return
    if addr.startswith("@"):
        addr = "\0" + addr[1:]
    try:
        import socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            sock.connect(addr)
            sock.sendall(message.encode())
        finally:
            sock.close()
    except OSError:
        pass


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class BlueWatchDaemon:
    """Main daemon process for Bluetooth scanning."""

    def __init__(self, adapter: Optional[str] = None, classic_adapter: Optional[str] = None, web_port: Optional[int] = None, metrics_port: Optional[int] = None):
        self.scanner = BluetoothScanner(adapter=adapter, classic_adapter=classic_adapter)
        self.running = False
        self.clients: list[asyncio.StreamWriter] = []
        self._server: asyncio.Server | None = None
        self._web_port = web_port
        self._web_server: WebServer | None = None
        self._notifications = NotificationManager()
        self._metrics = None
        self._metrics_port = metrics_port
        self._http_session: aiohttp.ClientSession | None = None
        self._start_time = time.monotonic()
        self._esp32_scanner: ESP32Scanner | None = None
        self._esp32_config: tuple[bool, str] | None = None
        self._last_scan_cycle = time.monotonic()

    @staticmethod
    async def _wait_for_bluetooth(max_wait: int = 120, interval: int = 5) -> None:
        """Wait for the macOS Bluetooth controller to be powered on.

        On macOS, launchd may start this daemon at login before
        CoreBluetooth has finished initialising.  We poll the
        ControllerPowerState pref (works on all modern macOS versions)
        to avoid the "adapter busy" errors that bleak raises when it
        tries to scan against a not-yet-ready adapter.

        This is a no-op on non-macOS platforms.
        """
        if platform.system() != "Darwin":
            return

        waited = 0
        logger.info("macOS detected – waiting for Bluetooth controller …")

        while waited < max_wait:
            try:
                result = await asyncio.to_thread(
                    subprocess.run,
                    [
                        "defaults", "read",
                        "/Library/Preferences/com.apple.Bluetooth",
                        "ControllerPowerState",
                    ],
                    capture_output=True, text=True, timeout=5,
                )
                power_state = result.stdout.strip()
                if power_state == "1":
                    logger.info(
                        "Bluetooth controller is on (waited %ds).", waited
                    )
                    # Extra grace period for CoreBluetooth framework
                    # initialisation after the controller reports ready.
                    await asyncio.sleep(3)
                    return
                else:
                    logger.debug(
                        "Bluetooth power state: %s (not ready yet)", power_state
                    )
            except Exception as exc:
                logger.debug("Bluetooth check failed: %s", exc)

            await asyncio.sleep(interval)
            waited += interval

        logger.warning(
            "Bluetooth not confirmed ready after %ds – proceeding anyway.", max_wait
        )

    async def start(self) -> None:
        """Start the daemon."""
        logger.info("Starting bluewatch daemon...")

        # Block until the Bluetooth adapter is ready (macOS only).
        await self._wait_for_bluetooth()

        if self.scanner._use_dual_adapter:
            logger.info(f"Dual-adapter mode: BLE on {self.scanner.adapter}, classic on {self.scanner.classic_adapter}")
        else:
            adapter = self.scanner.adapter or "auto"
            logger.info(f"Single-adapter mode: {adapter} (BLE and classic scans run sequentially)")

        # Initialize database
        await db.init_db()
        logger.info(f"Database initialized at {db.DB_PATH}")

        from .classifier import set_custom_types
        custom_types = await db.get_custom_types()
        set_custom_types([(t["key"], t["icon"], t["label"]) for t in custom_types])

        # Initialize notifications
        await self._notifications.start()

        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))

        # Start socket server for TUI communication
        await self._start_socket_server()

        # Start web server if port specified. A port saved in Config >
        # Operations overrides the --port CLI default -- lets the port be
        # changed from the web UI itself without editing the systemd unit,
        # though it only takes effect on the next restart (can't rebind the
        # listening socket the page you're editing is served from).
        if self._web_port:
            settings = await db.get_settings()
            effective_port = settings.web_port or self._web_port
            self._web_server = WebServer(port=effective_port, notifications=self._notifications, adapter=self.scanner.adapter, scanner=self.scanner)
            await self._web_server.start()
            logger.info(f"Web dashboard available at http://0.0.0.0:{effective_port}")

        # Start Prometheus metrics exporter (requires `pip install bluewatch[metrics]`)
        if self._metrics_port:
            try:
                from .prometheus import MetricsExporter
                self._metrics = MetricsExporter(port=self._metrics_port, version=__version__)
                self._metrics.start()
            except ImportError:
                logger.error("prometheus-client not installed. Install with: pip install bluewatch[metrics]")
                self._metrics = None

        # Start scanning and background loops
        self.running = True
        self._http_session = aiohttp.ClientSession()
        asyncio.create_task(self._absence_check_loop())
        asyncio.create_task(self._systemd_watchdog_loop())
        if self._metrics:
            asyncio.create_task(self._metrics_update_loop())
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._storage_prune_loop())
        await self.scanner.start_continuous_ble()
        asyncio.create_task(self._ble_continuous_manager())
        asyncio.create_task(self._esp32_scanner_manager())
        asyncio.create_task(self._esp32_ingest_loop())
        await self._scan_loop()

    async def _ble_continuous_manager(self) -> None:
        """Keeps continuous BLE scanning paused for as long as a Scan
        Unit poll is active, resuming it as soon as the poll clears --
        checked frequently so the pause/resume reacts quickly rather
        than waiting for the next scan-loop cycle boundary."""
        paused_for_scan_unit = False
        while self.running:
            want_paused = active_scan.SCAN_IN_PROGRESS.is_set()
            if want_paused and not paused_for_scan_unit:
                await self.scanner.stop_continuous_ble()
                paused_for_scan_unit = True
            elif not want_paused and paused_for_scan_unit:
                await self.scanner.start_continuous_ble()
                paused_for_scan_unit = False
            await asyncio.sleep(0.5)

    async def _systemd_watchdog_loop(self) -> None:
        """Pings systemd's watchdog (WatchdogSec in bluewatch.service)
        only while _scan_loop is actually still cycling -- if the BLE
        stack wedges on a D-Bus call that never raises or times out (so
        neither an exception nor a process exit ever happens), this
        simply stops pinging, and systemd kills and restarts the unit
        once WatchdogSec elapses instead of leaving a hung process
        serving a stale dashboard indefinitely. A no-op if the service
        isn't running under systemd (NOTIFY_SOCKET unset) or has no
        WatchdogSec configured."""
        interval = 15
        while self.running:
            if time.monotonic() - self._last_scan_cycle < interval * 2:
                _sd_notify("WATCHDOG=1")
            await asyncio.sleep(interval)

    async def _esp32_scanner_manager(self) -> None:
        """Starts, stops, or reconfigures the optional ESP32-S3 second BLE
        radio to match the operator's Config setting -- checked
        periodically so a toggle or host-address change in /config takes
        effect without a daemon restart."""
        while self.running:
            try:
                enabled, host = await db.get_esp32_scanner_settings()
                current = (enabled, host)
                if current != self._esp32_config:
                    if self._esp32_scanner is not None:
                        await self._esp32_scanner.stop()
                        self._esp32_scanner = None
                        active_scan.set_esp32_scanner(None)
                    if enabled:
                        self._esp32_scanner = ESP32Scanner(host=host, vendor_lookup=self.scanner._get_vendor)
                        self._esp32_scanner.start()
                        active_scan.set_esp32_scanner(self._esp32_scanner)
                    self._esp32_config = current
            except Exception as e:
                logger.warning(f"ESP32 scanner manager error: {e}")
            await asyncio.sleep(5)

    async def _esp32_ingest_loop(self) -> None:
        """Upserts whatever the ESP32 second radio has heard, on its own
        cadence -- deliberately NOT gated by active_scan.SCAN_IN_PROGRESS
        like _scan_loop is. That gate exists so the built-in adapter is
        freed up for an operator-triggered Scan Unit poll (BlueZ only
        allows one connect/discover at a time on it); the ESP32 is a
        separate USB radio that never contends for it, so pausing this
        loop too would just silently drop everything it heard for as
        long as the poll takes with no benefit."""
        while self.running:
            try:
                if self._esp32_scanner is not None and self._esp32_scanner.connected:
                    devices = await self._esp32_scanner.snapshot()
                    wigle_candidates = []
                    for device in devices:
                        db_device, is_new = await db.upsert_device(
                            mac=device.mac,
                            vendor=device.vendor,
                            friendly_name=device.name,
                            rssi=device.rssi,
                            service_uuids=device.service_uuids,
                            bt_type=device.bt_type,
                            device_class=device.device_class,
                            manufacturer_data=device.manufacturer_data,
                            service_data=device.service_data,
                            appearance=device.appearance,
                        )
                        if self._web_server is not None:
                            try:
                                await self._web_server.broadcast_sighting(_device_to_json(db_device))
                            except Exception as e:
                                logger.debug(f"Live-event broadcast failed: {e}")
                        await self._notifications.on_device_seen(db_device, is_new)
                        if not db_device.vendor and not is_randomized_mac(db_device.mac):
                            wigle_candidates.append(db_device.mac)
                    await self._try_wigle_lookups(wigle_candidates)
                    if devices:
                        await self._notify_clients({"event": "scan_complete", "count": len(devices)})
            except Exception as e:
                logger.error(f"ESP32 ingest error: {e}")
            await asyncio.sleep(SCAN_INTERVAL)

    async def stop(self) -> None:
        """Stop the daemon."""
        logger.info("Stopping bluewatch daemon...")
        self.running = False

        # Close all client connections
        for writer in self.clients:
            writer.close()
            await writer.wait_closed()

        # Close socket server
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        # Stop web server
        if self._web_server:
            await self._web_server.stop()

        # Stop notifications
        await self._notifications.stop()

        # Stop continuous BLE scanning
        await self.scanner.stop_continuous_ble()

        # Stop the optional ESP32 second scanner, if running
        if self._esp32_scanner is not None:
            await self._esp32_scanner.stop()
            self._esp32_scanner = None
            active_scan.set_esp32_scanner(None)

        # Close HTTP session
        if self._http_session:
            await self._http_session.close()

        # Remove socket file
        if SOCKET_PATH.exists():
            SOCKET_PATH.unlink()

        logger.info("Daemon stopped")

    async def _start_socket_server(self) -> None:
        """Start Unix socket server for TUI clients."""
        # Remove stale socket
        if SOCKET_PATH.exists():
            SOCKET_PATH.unlink()

        self._server = await asyncio.start_unix_server(
            self._handle_client,
            path=str(SOCKET_PATH)
        )
        # Make socket accessible
        os.chmod(SOCKET_PATH, 0o666)
        logger.info(f"Socket server listening at {SOCKET_PATH}")

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        """Handle a TUI client connection."""
        self.clients.append(writer)
        logger.info("TUI client connected")

        try:
            while self.running:
                data = await reader.readline()
                if not data:
                    break

                try:
                    request = json.loads(data.decode())
                    response = await self._handle_request(request)
                    writer.write(json.dumps(response).encode() + b"\n")
                    await writer.drain()
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from client")
                except Exception as e:
                    logger.error(f"Error handling request: {e}")

        except asyncio.CancelledError:
            pass
        finally:
            self.clients.remove(writer)
            writer.close()
            await writer.wait_closed()
            logger.info("TUI client disconnected")

    async def _handle_request(self, request: dict) -> dict:
        """Handle a request from a TUI client."""
        cmd = request.get("cmd")

        if cmd == "list":
            include_ignored = request.get("include_ignored", True)
            devices = await db.get_all_devices(include_ignored)

            # Auto-classify devices that don't have a type
            from .classifier import classify_device
            device_list = []
            for d in devices:
                device_type = d.device_type
                if not device_type:
                    device_type = classify_device(d.vendor, d.friendly_name, d.service_uuids, d.device_class, d.manufacturer_data, appearance=d.appearance, service_data=d.service_data, mac=d.mac)
                    # Store the auto-classified type
                    if device_type != "unknown":
                        await db.set_device_type(d.mac, device_type)

                device_list.append({
                    "mac": d.mac,
                    "vendor": d.vendor,
                    "friendly_name": d.friendly_name,
                    "device_type": device_type,
                    "ignored": d.ignored,
                    "first_seen": (d.first_seen.isoformat()) if d.first_seen else None,
                    "last_seen": (d.last_seen.isoformat()) if d.last_seen else None,
                    "total_sightings": d.total_sightings,
                })

            return {"status": "ok", "devices": device_list}

        elif cmd == "set_name":
            mac = request.get("mac")
            name = request.get("name")
            if mac and name is not None:
                await db.set_friendly_name(mac, name)
                return {"status": "ok"}
            return {"status": "error", "message": "Missing mac or name"}

        elif cmd == "set_ignored":
            mac = request.get("mac")
            ignored = request.get("ignored", False)
            if mac:
                await db.set_ignored(mac, ignored)
                return {"status": "ok"}
            return {"status": "error", "message": "Missing mac"}

        elif cmd == "set_device_type":
            mac = request.get("mac")
            device_type = request.get("device_type")
            if mac and device_type:
                await db.set_device_type(mac, device_type)
                return {"status": "ok"}
            return {"status": "error", "message": "Missing mac or device_type"}

        elif cmd == "get_device_types":
            from .classifier import get_all_types
            types = get_all_types()
            return {
                "status": "ok",
                "types": [{"id": t[0], "icon": t[1], "label": t[2]} for t in types]
            }

        elif cmd == "get_sightings":
            mac = request.get("mac")
            days = request.get("days", 30)
            if mac:
                sightings = await db.get_sightings(mac, days)
                return {
                    "status": "ok",
                    "sightings": [
                        {
                            "timestamp": s.timestamp.isoformat(),
                            "rssi": s.rssi,
                        }
                        for s in sightings
                    ]
                }
            return {"status": "error", "message": "Missing mac"}

        elif cmd == "get_hourly":
            mac = request.get("mac")
            days = request.get("days", 30)
            if mac:
                hourly = await db.get_hourly_distribution(mac, days)
                return {"status": "ok", "hourly": hourly}
            return {"status": "error", "message": "Missing mac"}

        elif cmd == "get_daily":
            mac = request.get("mac")
            days = request.get("days", 30)
            if mac:
                daily = await db.get_daily_distribution(mac, days)
                return {"status": "ok", "daily": daily}
            return {"status": "error", "message": "Missing mac"}

        elif cmd == "search":
            mac_filter = request.get("mac")
            start_time = request.get("start_time")
            end_time = request.get("end_time")

            # Parse datetime strings if provided
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_time) if start_time else None
            end_dt = datetime.fromisoformat(end_time) if end_time else None

            results = await db.search_devices(mac_filter, start_dt, end_dt)
            return {
                "status": "ok",
                "results": results,
            }

        elif cmd == "status":
            return {
                "status": "ok",
                "running": self.running,
                "clients": len(self.clients),
            }

        elif cmd == "set_notes":
            mac = request.get("mac")
            notes = request.get("notes")
            if mac:
                await db.set_device_notes(mac, notes)
                return {"status": "ok"}
            return {"status": "error", "message": "Missing mac"}

        elif cmd == "get_dwell_time":
            mac = request.get("mac")
            days = request.get("days", 30)
            gap_minutes = request.get("gap_minutes", 15)
            if mac:
                dwell = await db.get_dwell_time(mac, days, gap_minutes)
                return {"status": "ok", "dwell_time": dwell}
            return {"status": "error", "message": "Missing mac"}

        elif cmd == "get_correlated_devices":
            mac = request.get("mac")
            days = request.get("days", 30)
            window_minutes = request.get("window_minutes", 5)
            gap_minutes = request.get("gap_minutes", 15)
            edge_minutes = request.get("edge_minutes")
            if mac:
                correlated = await db.get_correlated_devices(
                    mac, days, window_minutes, gap_minutes, edge_minutes
                )
                return {"status": "ok", "correlated_devices": correlated}
            return {"status": "error", "message": "Missing mac"}

        elif cmd == "get_rotation_candidates":
            mac = request.get("mac")
            days = request.get("days", 7)
            if mac:
                rotation = await db.get_rotation_candidates(mac, days)
                return {"status": "ok", **rotation}
            return {"status": "error", "message": "Missing mac"}

        elif cmd == "get_name_groups":
            include_ignored = request.get("include_ignored", False)
            min_devices = request.get("min_devices", 2)
            groups = await db.get_name_groups(
                min_devices=min_devices, include_ignored=include_ignored
            )
            return {"status": "ok", "name_groups": groups}

        elif cmd == "get_proximity_stats":
            mac = request.get("mac")
            days = request.get("days", 7)
            if mac:
                stats = await db.get_proximity_stats(mac, days)
                return {"status": "ok", "proximity_stats": stats}
            return {"status": "error", "message": "Missing mac"}

        else:
            return {"status": "error", "message": f"Unknown command: {cmd}"}

    async def _scan_loop(self) -> None:
        """Main scanning loop."""
        logger.info(f"Starting scan loop (interval: {SCAN_INTERVAL}s)")

        while self.running:
            # Proves the loop itself is still executing each cycle (paused
            # for a Scan Unit poll counts too) -- consumed by
            # _systemd_watchdog_loop() below to tell "the process exists"
            # apart from "the scan loop is actually alive", since a BLE
            # D-Bus call hanging forever wouldn't raise or exit and so
            # wouldn't trigger Restart=always on its own.
            self._last_scan_cycle = time.monotonic()
            try:
                # An operator-triggered Scan Unit poll gets priority over
                # the background sweep -- skip starting a new passive
                # cycle while one is active rather than competing with it
                # for the adapter (BlueZ only allows one connect/discover
                # at a time on a single-adapter host).
                if active_scan.SCAN_IN_PROGRESS.is_set():
                    await asyncio.sleep(1)
                    continue

                start_ts = time.monotonic()
                devices = await self.scanner.scan()
                duration = time.monotonic() - start_ts

                new_count = 0
                wigle_candidates = []
                for device in devices:
                    db_device, is_new = await db.upsert_device(
                        mac=device.mac,
                        vendor=device.vendor,
                        friendly_name=device.name,
                        rssi=device.rssi,
                        service_uuids=device.service_uuids,
                        bt_type=device.bt_type,
                        device_class=device.device_class,
                        manufacturer_data=device.manufacturer_data,
                        service_data=device.service_data,
                        appearance=device.appearance,
                    )
                    if is_new:
                        new_count += 1

                    # Push to any open dashboard immediately -- see
                    # WebServer.broadcast_sighting's comment. Best-effort:
                    # a bad payload or a dead SSE client must never break
                    # scanning itself.
                    if self._web_server is not None:
                        try:
                            await self._web_server.broadcast_sighting(_device_to_json(db_device))
                        except Exception as e:
                            logger.debug(f"Live-event broadcast failed: {e}")

                    # Trigger notification checks
                    await self._notifications.on_device_seen(db_device, is_new)

                    # A randomized MAC has no fixed vendor to find and a
                    # WiGLE record for it would belong to a past rotation,
                    # not this device -- only exact/fixed addresses qualify.
                    if not db_device.vendor and not is_randomized_mac(db_device.mac):
                        wigle_candidates.append(db_device.mac)

                await self._try_wigle_lookups(wigle_candidates)

                ble_count = sum(1 for d in devices if d.bt_type == "ble")
                self.scanner.check_zero_ble_streak(ble_count)

                if self._metrics:
                    classic_count = sum(1 for d in devices if d.bt_type == "classic")
                    self._metrics.on_scan_complete(devices, ble_count, classic_count, duration, new_count)

                # Notify connected clients
                await self._notify_clients({
                    "event": "scan_complete",
                    "count": len(devices),
                })

            except Exception as e:
                logger.error(f"Scan error: {e}")
                if self._metrics:
                    self._metrics.on_scan_error("scan")

            await asyncio.sleep(SCAN_INTERVAL)

    # WiGLE's free tier has a very small daily query quota, so at most this
    # many *new* lookups are spent per scan cycle regardless of how many
    # vendor-less devices showed up in it -- the rest wait for a later cycle.
    _WIGLE_LOOKUPS_PER_CYCLE = 1

    async def _try_wigle_lookups(self, candidate_macs: list[str]) -> None:
        """Spend a small, fixed budget of WiGLE lookups on devices we still
        have no vendor for, skipping anything already checked before."""
        if not candidate_macs:
            return
        credentials = await db.get_wigle_credentials()
        if not credentials:
            return
        api_name, api_token = credentials

        spent = 0
        for mac in candidate_macs:
            if spent >= self._WIGLE_LOOKUPS_PER_CYCLE:
                break
            if await db.get_wigle_cache_entry(mac) is not None:
                continue  # already checked (found or not) -- never re-spend quota on it
            spent += 1
            vendor = await wigle.lookup_vendor(mac, api_name, api_token)
            await db.set_wigle_cache_entry(mac, vendor)
            if vendor:
                await db.set_device_vendor(mac, vendor)
                logger.info(f"WiGLE resolved vendor for {mac}: {vendor}")

    async def _metrics_update_loop(self) -> None:
        """Periodically update database-derived metrics."""
        while self.running:
            try:
                if self._metrics:
                    await self._metrics.update_db_metrics()
            except Exception as e:
                logger.warning(f"Metrics update error: {e}")
            await asyncio.sleep(60)

    async def _absence_check_loop(self) -> None:
        """Periodically check for absent watched devices."""
        while self.running:
            try:
                await self._notifications.check_absent_devices()
            except Exception as e:
                logger.error(f"Absence check error: {e}")
            await asyncio.sleep(60)  # Check every minute

    async def _heartbeat_loop(self) -> None:
        """Periodically POST a heartbeat to the configured URL."""
        while self.running:
            try:
                settings = await db.get_settings()
                url = settings.heartbeat_url
                interval = settings.heartbeat_interval
                if url:
                    device_count = len(await db.get_all_devices(include_ignored=True))
                    payload = {
                        "hostname": platform.node(),
                        "uptime_seconds": int(time.monotonic() - self._start_time),
                        "device_count": device_count,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "version": __version__,
                    }
                    async with self._http_session.post(
                        url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        if resp.status >= 400:
                            logger.warning(f"Heartbeat returned HTTP {resp.status}")
                    await asyncio.sleep(interval)
                else:
                    await asyncio.sleep(60)  # Re-check for config changes
            except Exception as e:
                logger.warning(f"Heartbeat failed: {e}")
                await asyncio.sleep(60)

    async def _storage_prune_loop(self) -> None:
        """Periodically prune old sightings to free storage."""
        while self.running:
            try:
                settings = await db.get_settings()
                prune_days = settings.prune_days
                min_sightings = settings.prune_min_sightings
                if prune_days > 0:
                    if min_sightings > 0:
                        # Remove whole stale devices (and their sightings) that
                        # were last seen >prune_days ago and seen <min_sightings times.
                        deleted = await db.prune_stale_devices(prune_days, min_sightings)
                        if deleted:
                            logger.info(
                                f"Pruned {deleted} stale devices "
                                f"(older than {prune_days} days, fewer than {min_sightings} sightings)"
                            )
                    else:
                        # Age-only: trim old sighting rows, keep device records.
                        deleted = await db.cleanup_old_sightings(prune_days)
                        if deleted:
                            logger.info(f"Pruned {deleted} sightings older than {prune_days} days")
                    # Pruning frees pages inside the database file but doesn't
                    # shrink it; reclaim the disk space once enough has built up.
                    reclaimed = await db.vacuum_if_fragmented()
                    if reclaimed:
                        logger.info(f"Vacuumed database, reclaimed ~{reclaimed} MB on disk")
                    await asyncio.sleep(3600)  # Once per hour
                else:
                    await asyncio.sleep(300)  # Re-check for config changes
            except Exception as e:
                logger.warning(f"Storage prune error: {e}")
                await asyncio.sleep(300)

    async def _notify_clients(self, event: dict) -> None:
        """Send an event to all connected clients."""
        data = json.dumps(event).encode() + b"\n"
        for writer in self.clients:
            try:
                writer.write(data)
                await writer.drain()
            except Exception:
                pass  # Client might have disconnected


def main() -> None:
    """Entry point for bluewatch-daemon."""
    parser = argparse.ArgumentParser(
        description="BlueWatch Bluetooth neighborhood monitor daemon"
    )
    parser.add_argument(
        "-a", "--adapter",
        help="Bluetooth adapter for BLE scanning (e.g., hci0)"
    )
    parser.add_argument(
        "--classic-adapter",
        help="Separate adapter for classic Bluetooth scanning (e.g., hci1). "
             "When set to a different adapter, BLE and classic scans run concurrently."
    )
    parser.add_argument(
        "-l", "--list-adapters",
        action="store_true",
        help="List available Bluetooth adapters and exit"
    )
    parser.add_argument(
        "--no-web",
        action="store_true",
        help="Disable web dashboard"
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8080,
        help="Web dashboard port (default: 8080)"
    )
    parser.add_argument(
        "--metrics-port",
        type=int,
        default=None,
        help="Prometheus metrics port (default: disabled, env: BLUEWATCH_METRICS_PORT)"
    )
    args = parser.parse_args()

    if args.list_adapters:
        adapters = list_adapters()
        if adapters:
            print("Available Bluetooth adapters:")
            for adapter in adapters:
                print(f"  {adapter.name}: {adapter.address} ({adapter.alias})")
        else:
            print("No Bluetooth adapters found")
        return

    web_port = None if args.no_web else args.port
    metrics_port = args.metrics_port or METRICS_PORT
    daemon = BlueWatchDaemon(adapter=args.adapter, classic_adapter=args.classic_adapter, web_port=web_port, metrics_port=metrics_port)
    try:
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
