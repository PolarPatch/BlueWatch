"""Notification system using ntfy.sh for push notifications."""

import asyncio
import logging
from collections import deque
from datetime import datetime, timedelta
from typing import Optional

import aiohttp

from . import db
from .classifier import (
    TYPE_TRACKER, COMPANY_ID_APPLE, COMPANY_ID_MICROSOFT, COMPANY_ID_SAMSUNG,
    _walk_apple_tlvs, _short_uuid,
)
from .db import Device, Settings

logger = logging.getLogger(__name__)

# Payloads that make a phone show a pairing popup -- what BLE spam tools
# (Flipper "BLE spam", ESP32 AppleJuice and similar) broadcast:
# Apple Proximity Pairing (0x07) and Nearby Action (0x0F), Microsoft Swift
# Pair (Beacon ID 0x03), Samsung EasySetup buds/watch popups, and Google
# Fast Pair (service 0xFE2C). Ordinary Apple traffic (Nearby Info 0x10,
# Find My 0x12, AirPlay 0x09, ...) is not a popup and is not counted.
_APPLE_POPUP_TYPES = frozenset({0x07, 0x0F})
_MS_SWIFT_PAIR_BEACON_ID = 0x03
_SAMSUNG_POPUP_PREFIXES = (
    bytes.fromhex("42098102141503210109"),  # EasySetup buds
    bytes.fromhex("010002000101ff000043"),  # EasySetup watch
)
_FAST_PAIR_SHORT_UUID = 0xFE2C


def _is_pairing_popup_advert(device: Device) -> bool:
    mfg = device.manufacturer_data or {}
    apple = mfg.get(COMPANY_ID_APPLE)
    if apple and any(t in _APPLE_POPUP_TYPES for t, _ in _walk_apple_tlvs(apple)):
        return True
    ms = mfg.get(COMPANY_ID_MICROSOFT)
    if ms and ms[:1] == bytes([_MS_SWIFT_PAIR_BEACON_ID]):
        return True
    samsung = mfg.get(COMPANY_ID_SAMSUNG)
    if samsung and samsung.startswith(_SAMSUNG_POPUP_PREFIXES):
        return True
    return any(_short_uuid(u) == _FAST_PAIR_SHORT_UUID for u in (device.service_data or {}))


# Minimum gap between two notifications of the same noisy kind.
NOISY_ALERT_COOLDOWN = timedelta(minutes=30)

# ntfy.sh base URL
NTFY_BASE_URL = "https://ntfy.sh"


class NotificationManager:
    """Manages push notifications via ntfy.sh."""

    def __init__(self):
        self._settings: Optional[Settings] = None
        self._watched_last_seen: dict[str, datetime] = {}  # MAC -> last seen time
        # MAC -> when it was seen just before the current sighting. The Device
        # handed to on_device_seen() already carries the *updated* last_seen, so
        # the gap since the previous sighting can't be read from it.
        self._prev_seen: dict[str, datetime] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        # BLE spam/flood detection: timestamps of recent pairing-popup-style
        # advertisements (Apple Continuity/Fast Pair/Swift Pair/Samsung),
        # system-wide -- not per-MAC, since a flood attack typically cycles
        # through many randomized source addresses rather than reusing one.
        # In-memory only (reset on restart, same as _prev_seen conceptually,
        # though that one reloads from DB) -- a burst is a live-moment signal,
        # nothing meaningful to persist about it across a restart.
        self._pairing_burst: deque[tuple[datetime, str]] = deque()
        self._ble_spam_flood_active = False  # true while over threshold, so we alert once per burst, not every sighting
        # Tracker "FOLLOW" alert: MACs already alerted for this run, so a
        # lingering tracker notifies once rather than on every sighting
        # once past threshold. In-memory only -- see class docstring below
        # for the accepted tradeoff (may re-alert once after a restart).
        self._tracker_follow_alerted: set[str] = set()
        # Rate limit for the noisy alert kinds (flood, tracker lingering):
        # key -> time of the last notification actually sent, and how many
        # were held back since then (reported in the next one that goes out).
        self._cooldown_last_sent: dict[str, datetime] = {}
        self._cooldown_suppressed: dict[str, int] = {}

    async def start(self) -> None:
        """Initialize the notification manager."""
        self._settings = await db.get_settings()
        self._session = aiohttp.ClientSession()

        self._prev_seen = await db.get_last_seen_map()

        # Load current state of watched devices
        watched = await db.get_watched_devices()
        for device in watched:
            if device.last_seen:
                self._watched_last_seen[device.mac] = device.last_seen

        logger.info(f"Notification manager started (enabled={self._settings.ntfy_enabled})")

    async def stop(self) -> None:
        """Cleanup the notification manager."""
        if self._session:
            await self._session.close()
            self._session = None
        logger.info("Notification manager stopped")

    async def reload_settings(self) -> None:
        """Reload settings from database."""
        self._settings = await db.get_settings()
        logger.info(f"Notification settings reloaded (enabled={self._settings.ntfy_enabled})")

    async def _send_notification(
        self,
        title: str,
        message: str,
        priority: int = 3,
        tags: Optional[list[str]] = None,
        cooldown_key: Optional[str] = None,
    ) -> bool:
        """Send a notification via ntfy.sh.

        Priority levels: 1=min, 2=low, 3=default, 4=high, 5=urgent

        With a cooldown_key, at most one notification per key goes out per
        NOISY_ALERT_COOLDOWN; the rest are counted and mentioned in the next
        one, so a busy area can't flood the phone.
        """
        if not self._settings or not self._settings.ntfy_enabled:
            return False

        if cooldown_key:
            now = datetime.now()
            last = self._cooldown_last_sent.get(cooldown_key)
            if last and now - last < NOISY_ALERT_COOLDOWN:
                self._cooldown_suppressed[cooldown_key] = self._cooldown_suppressed.get(cooldown_key, 0) + 1
                logger.info(f"Notification held back (cooldown): {title}")
                return False
            held = self._cooldown_suppressed.pop(cooldown_key, 0)
            if held:
                message += f"\n(+{held} more like this in the last {int(NOISY_ALERT_COOLDOWN.total_seconds() // 60)} min, not sent)"
            self._cooldown_last_sent[cooldown_key] = now

        if not self._settings.ntfy_topic:
            logger.warning("Notifications enabled but no topic configured")
            return False

        if not self._session:
            self._session = aiohttp.ClientSession()

        url = f"{NTFY_BASE_URL}/{self._settings.ntfy_topic}"

        headers = {
            "Title": title,
            "Priority": str(priority),
        }
        if tags:
            headers["Tags"] = ",".join(tags)

        try:
            async with self._session.post(
                url,
                data=message,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    logger.info(f"Notification sent: {title}")
                    return True
                else:
                    logger.warning(f"Notification failed: {response.status}")
                    return False
        except asyncio.TimeoutError:
            logger.warning("Notification timeout")
            return False
        except Exception as e:
            logger.error(f"Notification error: {e}")
            return False

    async def on_device_seen(self, device: Device, is_new: bool) -> None:
        """Handle a device being seen during a scan.

        This is called after every device sighting to check for notification triggers.

        Per-device notify_arrive overrides (set via the category/detail
        panel) take full precedence over the default behavior below --
        True fires an "Arrived" notification on genuine arrival events
        (first-ever sighting, or reappearing after an absence gap), False
        explicitly silences the device (skips the default new-device /
        watched-return logic entirely), and None (no override) falls
        through to the unchanged default behavior.
        """
        if not self._settings or not self._settings.ntfy_enabled:
            return

        now = datetime.now()
        prev_seen = self._prev_seen.get(device.mac)
        self._prev_seen[device.mac] = now

        # Type-based alert (e.g. "a Flipper Zero is nearby") -- independent
        # of categorization/watch state below, since the security relevance
        # of a device *type* showing up doesn't go away once it's been
        # triaged into a category. Fires on first sighting, and again after
        # a return-worthy absence gap (measured from prev_seen, see above),
        # so it doesn't spam on every single advertisement of a device that's
        # continuously present.
        # The stored device_type column is only set by a manual override --
        # automatic classification is computed on the fly -- so use the same
        # computed type the dashboard shows, or a Flipper/drone/camera that
        # was never manually typed would never trigger this alert.
        from .classifier import classify_device, get_type_label
        device_type = device.device_type or classify_device(
            device.vendor,
            device.friendly_name,
            device.service_uuids,
            device.device_class,
            device.manufacturer_data,
            appearance=device.appearance,
            service_data=device.service_data,
            mac=device.mac,
        )
        type_alert_sent = False
        if device_type and device_type in self._settings.type_alert_types:
            should_alert = is_new
            if not should_alert and prev_seen is not None:
                gap_minutes = (now - prev_seen).total_seconds() / 60
                should_alert = gap_minutes >= self._settings.watched_return_minutes
            if should_alert:
                type_alert_sent = True
                type_label = get_type_label(device_type)
                name = device.friendly_name or device.vendor or device.mac
                await self._send_notification(
                    title=f"⚠ {type_label} detected nearby",
                    message=f"{name} ({device.mac})",
                    priority=5,
                    tags=["warning", "bluetooth"],
                )

        # BLE advertisement-flood ("spam") detection -- independent of
        # categorization/watch state, same reasoning as the type alert
        # above. See _check_ble_spam_flood()'s own docstring.
        await self._check_ble_spam_flood(device, now)

        # Tracker persistence ("FOLLOW") alert -- also independent of
        # categorization, and deliberately checked even for a device the
        # operator has already silenced/grouped, since a planted tracker
        # lingering nearby is worth flagging regardless of triage state.
        if device_type == TYPE_TRACKER:
            await self._check_tracker_follow(device)

        arrive_override = db.notify_mode_active(device.notify_arrive, device.notify_arrive_expires_at)
        if arrive_override is not None:
            if arrive_override:
                gap_minutes = self._settings.watched_return_minutes
                is_arrival = is_new or (
                    prev_seen is not None
                    and (now - prev_seen).total_seconds() / 60 >= gap_minutes
                )
                if is_arrival:
                    name = device.friendly_name or device.vendor or device.mac
                    await self._send_notification(
                        title="Device Arrived",
                        message=f"{name} ({device.mac})",
                        priority=4,
                        tags=["house", "bluetooth"],
                    )
                    if is_new:
                        await db.mark_new_device_notified(device.mac)
            # arrive_override is False (explicitly silenced) or True-but-not-
            # an-arrival-event: either way, skip the default logic below.
            self._watched_last_seen[device.mac] = now
            return

        # No per-device override. Known/categorized devices (group_id set)
        # are silent by default -- that's the entire point of categorizing
        # them -- so the legacy new-device / watched-return behavior below
        # only applies to still-Unknown (uncategorized) devices.
        if device.group_id is not None:
            self._watched_last_seen[device.mac] = now
            return

        # Check for new device notification
        if self._settings.notify_new_device and not device.new_device_notified:
            threshold = self._settings.new_device_threshold_minutes
            name = device.friendly_name or device.vendor or device.mac

            if threshold == 0 and is_new:
                # Immediate mode: notify on first sighting
                await self._send_notification(
                    title="New Device Detected",
                    message=f"{name} ({device.mac})\nType: {device.device_type or 'Unknown'}",
                    priority=3,
                    tags=["new", "bluetooth"],
                )
                await db.mark_new_device_notified(device.mac)
                return
            elif threshold > 0 and not is_new and device.first_seen:
                # Deferred mode: notify once device has persisted long enough
                elapsed = (now - device.first_seen).total_seconds() / 60
                if elapsed >= threshold:
                    duration_str = self._format_duration(elapsed)
                    await self._send_notification(
                        title="Persistent Device Detected",
                        message=f"{name} ({device.mac})\nPresent for {duration_str}\nType: {device.device_type or 'Unknown'}",
                        priority=4,
                        tags=["warning", "bluetooth"],
                    )
                    await db.mark_new_device_notified(device.mac)
                    return

        # Check for watched device notifications
        if device.watched:
            prev_seen = self._watched_last_seen.get(device.mac)

            if prev_seen:
                minutes_absent = (now - prev_seen).total_seconds() / 60

                # Device returning after absence
                # (Skipped when the type alert above already announced this
                # same return, so a watched Flipper doesn't notify twice.)
                if (self._settings.notify_watched_return and
                        not type_alert_sent and
                        minutes_absent >= self._settings.watched_return_minutes):
                    name = device.friendly_name or device.vendor or device.mac
                    absence_str = self._format_duration(minutes_absent)
                    await self._send_notification(
                        title="Watched Device Returned",
                        message=f"{name} is back\nWas absent for {absence_str}",
                        priority=4,
                        tags=["loudspeaker", "bluetooth"],
                    )

            # Update last seen time
            self._watched_last_seen[device.mac] = now

    async def _check_ble_spam_flood(self, device: Device, now: datetime) -> None:
        """Flag a burst of pairing-popup-style BLE advertisements
        (Apple Continuity, Microsoft Swift Pair, Samsung) system-wide --
        the same signal AWOKxDAG's "BLE Spam Watch" uses for fake-
        pairing-popup spam attacks against nearby phones. Passive: this
        only counts advertisements already being received (BlueWatch
        never transmits), same as every other check in this file.

        Counted by *advertisement type*, not by MAC, since a flood attack
        typically cycles through many randomized source addresses rather
        than reusing one -- counting per-MAC would miss it entirely.
        Fast Pair (service_data 0xFE2C) isn't included: it's normally a
        one-shot advertisement while a real earbud case is open, already
        rare enough that it wouldn't meaningfully add signal here, and
        would need parsing service_data keys rather than a simple company
        ID check.
        """
        if not self._settings.ble_spam_alert_enabled:
            return
        # Only actual pairing-popup payloads count, and each address once per
        # window. (No randomized-address filter: spam tools often use BLE
        # random static addresses, which only sometimes have the
        # locally-administered bit that is_randomized_mac() checks.) Counting every Apple sighting
        # fired this alert about every 2 minutes in a normal busy area
        # (300+ iPhones/AirTags in 5 minutes, zero popup adverts), 2026-10-09.
        if not _is_pairing_popup_advert(device):
            return

        window = timedelta(seconds=self._settings.ble_spam_window_seconds)
        self._pairing_burst.append((now, device.mac))
        while self._pairing_burst and now - self._pairing_burst[0][0] > window:
            self._pairing_burst.popleft()

        count = len({mac for _, mac in self._pairing_burst})
        threshold = self._settings.ble_spam_threshold
        if count >= threshold and not self._ble_spam_flood_active:
            self._ble_spam_flood_active = True
            await self._send_notification(
                title="⚠ Possible BLE advertisement flood",
                message=f"{count} addresses sending pairing-popup adverts in the last {self._settings.ble_spam_window_seconds}s -- may be a spam/DoS attack against nearby phones, or just an unusually busy moment.",
                priority=4,
                tags=["warning", "bluetooth"],
                cooldown_key="ble_flood",
            )
        elif count < threshold // 2:
            # Rearm once the rate has clearly dropped, not the instant it
            # dips below threshold -- avoids re-alerting on every sighting
            # while a burst hovers right at the line.
            self._ble_spam_flood_active = False

    async def _check_tracker_follow(self, device: Device) -> None:
        """Flag a Find My/Tile/SmartTag-type device (TYPE_TRACKER) that has
        lingered far longer than a passerby would -- AWOKxDAG's own name
        ("FOLLOW") for this signal. Deliberately rarer and slower than the
        generic type_alert_types alert (which fires on every reappearance):
        this fires once, only after real persistence is established, since
        that's the actual privacy-relevant case (a planted tracker) rather
        than a stranger's AirTag passing by once.
        """
        if not self._settings.tracker_follow_alert_enabled:
            return
        if device.mac in self._tracker_follow_alerted:
            return
        # A tracker the operator has already filed in a category (their own,
        # a neighbour's) is known, so it doesn't need a lingering alert.
        if device.group_id is not None:
            return
        if device.total_sightings < self._settings.tracker_follow_min_sightings:
            return
        if not device.first_seen or not device.last_seen:
            return
        span_minutes = (device.last_seen - device.first_seen).total_seconds() / 60
        if span_minutes < self._settings.tracker_follow_min_minutes:
            return

        self._tracker_follow_alerted.add(device.mac)
        name = device.friendly_name or device.vendor or device.mac
        span_str = self._format_duration(span_minutes)
        await self._send_notification(
            title="⚠ Tracker lingering nearby",
            message=f"{name} ({device.mac}) has been detected {device.total_sightings} times over {span_str} -- worth checking it isn't a planted tracker.",
            priority=5,
            tags=["warning", "bluetooth"],
            cooldown_key="tracker_follow",
        )

    async def check_absent_devices(self) -> None:
        """Check for devices that have been absent too long.

        This should be called periodically (e.g., every minute). Devices
        with an explicit per-device notify_depart override are handled
        separately from (and take precedence over) the default
        watched-device-leave behavior below.
        """
        if not self._settings or not self._settings.ntfy_enabled:
            return

        now = datetime.now()
        threshold = timedelta(minutes=self._settings.watched_absence_minutes)

        overridden = await db.get_devices_with_notify_override()
        overridden_macs = {d.mac for d in overridden if d.notify_depart is not None}

        for device in overridden:
            if device.notify_depart is None or not device.last_seen:
                continue
            depart_override = db.notify_mode_active(device.notify_depart, device.notify_depart_expires_at)
            if depart_override is not True:
                continue  # False (explicitly silenced) or lapsed temp -> no depart notification
            if now - device.last_seen < threshold:
                continue
            notified_key = f"notified_absent_{device.mac}"
            last_notified = self._watched_last_seen.get(notified_key)
            if last_notified and (now - last_notified).total_seconds() < 3600:
                continue
            name = device.friendly_name or device.vendor or device.mac
            absence_str = self._format_duration((now - device.last_seen).total_seconds() / 60)
            await self._send_notification(
                title="Device Left",
                message=f"{name} hasn't been seen for {absence_str}",
                priority=3,
                tags=["wave", "bluetooth"],
            )
            self._watched_last_seen[notified_key] = now

        if not self._settings.notify_watched_leave:
            return

        # Default behavior (unchanged) for watched devices that don't have
        # their own explicit notify_depart override.
        watched = await db.get_watched_devices()

        for device in watched:
            if device.mac in overridden_macs or not device.last_seen:
                continue
            if device.group_id is not None:
                continue  # categorized devices are silent by default; use an explicit override to hear from them

            # Check if device has been absent longer than threshold
            if now - device.last_seen >= threshold:
                # Only notify once per absence (check if we already notified)
                notified_key = f"notified_absent_{device.mac}"
                last_notified = self._watched_last_seen.get(notified_key)

                if last_notified and (now - last_notified).total_seconds() < 3600:
                    # Already notified within the last hour
                    continue

                name = device.friendly_name or device.vendor or device.mac
                absence_str = self._format_duration(
                    (now - device.last_seen).total_seconds() / 60
                )
                await self._send_notification(
                    title="Watched Device Left",
                    message=f"{name} hasn't been seen for {absence_str}",
                    priority=3,
                    tags=["wave", "bluetooth"],
                )

                # Mark as notified
                self._watched_last_seen[notified_key] = now

    def _format_duration(self, minutes: float) -> str:
        """Format a duration in minutes to a human-readable string."""
        if minutes < 60:
            return f"{int(minutes)} minutes"
        elif minutes < 1440:
            hours = minutes / 60
            return f"{hours:.1f} hours"
        else:
            days = minutes / 1440
            return f"{days:.1f} days"

    def update_watched_state(self, mac: str, watched: bool) -> None:
        """Update internal state when a device's watched status changes."""
        if watched:
            self._watched_last_seen[mac] = datetime.now()
        else:
            self._watched_last_seen.pop(mac, None)
            self._watched_last_seen.pop(f"notified_absent_{mac}", None)
