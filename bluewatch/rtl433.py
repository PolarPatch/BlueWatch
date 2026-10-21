"""Optional sub-GHz (433/868 MHz ISM band) discovery via rtl_433 and an
RTL-SDR dongle -- receive only, never transmits anything. Off entirely
unless the `rtl_433` binary and an RTL-SDR are both present; nothing
changes for anyone without this hardware.

Why this exists: TPMS sensors, weather stations, doorbells, garage
remotes, utility meters (Wireless M-Bus, electricity/water/heat) and much
else that never touches Bluetooth or Wi-Fi still leaks information on
433/868 MHz. rtl_433 (https://github.com/merbanan/rtl_433, GPL-2.0)
already decodes 200+ of these protocols; this module runs it as a
subprocess and feeds its JSON output into the same devices table
Bluetooth and mDNS/LAN devices already share, keyed like LAN devices are
(no MAC address exists here either) rather than reimplementing any of the
actual signal decoding.

A parked car's TPMS burst is often more identifying than its key fob: the
fob is usually a rolling code rtl_433 can detect but not attribute to a
brand, while many TPMS protocols are brand-specific (rtl_433 decodes them
as e.g. "Ford", "Toyota", ...), so it can answer "which car just parked
here" better than trying to decode the fob itself.
"""

import asyncio
import json
import logging
import shutil
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Hopped in one rtl_433 process (-H seconds between retunes) rather than two
# processes fighting over the one dongle. 433.92 MHz (Europe's the ISM band
# almost everything -- TPMS, weather stations, remotes -- actually uses) is
# checked first and more often; 868 MHz gets a share too since some newer
# sensors/doorbells use it, and it's also where Wireless M-Bus (utility
# meters -- electricity, water, heat) lives, Mode S/T specifically at
# 868.3M/1000k, same frequency already hopped here.
RTL433_FREQUENCIES = ["433.92M", "868.3M"]
RTL433_HOP_SECONDS = 30
# 1000k (rather than rtl_433's newer, lower "-Y classic" default) so Wireless
# M-Bus Mode S/T -- which needs 1000k -- decodes alongside everything else;
# confirmed live that weather stations (Nexus-TH) still decode fine at this
# rate too, so one samplerate covers both without a second dedicated pass.
RTL433_SAMPLE_RATE = "1000k"

# Utility meters by region (Config > RTL-SDR > Utility meters). rtl_433
# already has the decoders on by default; what a region adds is the
# frequencies those meters send on, and 1200k, which Wireless M-Bus Mode
# C/T and Badger ORION need (the other protocols decode fine at it too).
#   eu: Wireless M-Bus C/T at 868.95 MHz (most water/heat/gas meters and
#       many electricity meters; Mode S/T at 868.3 MHz is already hopped).
#   na: Itron ERT SCM/IDM and Neptune R900 around 912.6 MHz, Badger ORION
#       at 916.45 MHz (the US/Canada 902-928 MHz band).
# One dongle hears one band at a time, so a region adds frequencies to the
# hop rather than replacing it. Source: merbanan/rtl_433 protocol list.
METER_REGIONS = {
    "eu": ["868.95M"],
    "na": ["912.6M", "916.45M"],
}
METER_SAMPLE_RATE = "1200k"

# rtl_433 model names of utility meters and energy monitors (taken from
# rtl_433 25.02's decoders). Matched by prefix, case-insensitive.
METER_MODEL_PREFIXES = (
    "wireless-mbus", "ert-scm", "scmplus", "idm", "netidm", "neptune-r900",
    "badger-orion", "mueller-hotrod", "aradmsmeter", "flowis", "landisgyr-gs",
    "ikea-sparsnas", "efergy", "currentcost", "emontx", "esa-x000", "elv-em1000",
    "esic-emt7110", "clipsal-cmr113", "blueline-powercost", "geo-minim", "revolt-",
)

# What is kept of a meter's decode: who and what it is, never what it
# reads. Consumption and power say when a home is in use, so they are not
# stored or shown. Everything else rtl_433 reports is dropped.
METER_KEEP_KEYS = frozenset({
    "model", "id", "channel", "M", "manufacturer", "version", "type", "type_string",
    "ert_type", "ERTType", "ERTSerialNumber", "meter_type", "battery_ok", "tamper",
    "physical_tamper", "encoder_tamper", "leak", "rssi", "snr", "noise", "freq",
    "freq1", "freq2", "mod",
})


def is_meter_model(model: Optional[str]) -> bool:
    return bool(model) and model.lower().startswith(METER_MODEL_PREFIXES)


def meter_safe(data: dict) -> dict:
    """A meter decode with readings removed (see METER_KEEP_KEYS). Other
    devices pass through unchanged."""
    if not is_meter_model(data.get("model")):
        return data
    return {k: v for k, v in data.items() if k in METER_KEEP_KEYS}


def hop_plan(frequencies: list[str], meters: Optional[str]) -> tuple[list[str], str]:
    """The frequencies to hop and the sample rate, with a meter region's
    frequencies added."""
    freqs = list(frequencies)
    extra = METER_REGIONS.get(meters or "")
    if not extra:
        return freqs, RTL433_SAMPLE_RATE
    for freq in extra:
        if freq not in freqs:
            freqs.append(freq)
    return freqs, METER_SAMPLE_RATE


@dataclass
class Rtl433Device:
    key: str            # synthetic identifier, e.g. "RF:LaCrosse-TX141:12"
    label: str           # human-readable, e.g. "LaCrosse-TX141"
    model: str           # raw rtl_433 "model" field
    rssi: Optional[float]
    raw: dict             # the full decoded JSON, for classification/notes


def _binary_available() -> bool:
    return shutil.which("rtl_433") is not None


def _device_key(data: dict) -> Optional[str]:
    """A stable per-device identifier from rtl_433's decoded fields. Most
    protocols carry an `id`; a few only have `channel`. No both -> no
    stable identity, skip it rather than guessing (a random confidence
    field or the raw hex payload changes checksum-only bits reading to
    reading and would create a new "device" almost every time)."""
    model = data.get("model")
    if not model:
        return None
    ident = data.get("id")
    if ident is None:
        ident = data.get("ERTSerialNumber")  # ERT IDM meters have no id
    if ident is None:
        ident = data.get("channel")
    if ident is None:
        return None
    return f"RF:{model}:{ident}"


class Rtl433Scanner:
    """Runs `rtl_433 -F json`, hopping between RTL433_FREQUENCIES, and
    yields decoded devices. One instance per daemon; receive-only."""

    def __init__(self) -> None:
        self._proc: Optional[asyncio.subprocess.Process] = None

    async def start(self, frequencies: Optional[list[str]] = None, meters: Optional[str] = None) -> bool:
        if not _binary_available():
            logger.info("rtl_433 not installed -- sub-GHz (433/868 MHz) discovery skipped")
            return False
        freqs, sample_rate = hop_plan(frequencies or RTL433_FREQUENCIES, meters)
        # -M level adds rssi/snr/noise (dB) to every decode; without it
        # rtl_433 reports no signal strength at all (issue #8).
        args = ["rtl_433", "-F", "json", "-M", "level", "-s", sample_rate]
        for freq in freqs:
            args += ["-f", freq]
        if len(freqs) > 1:
            args += ["-H", str(RTL433_HOP_SECONDS)]
        try:
            self._proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            logger.info("rtl_433 not installed -- sub-GHz (433/868 MHz) discovery skipped")
            return False
        # A missing/unplugged RTL-SDR makes rtl_433 exit almost immediately
        # (device-open failure) rather than hang -- give it a moment and
        # check, so a dongle-less Pi logs one clear line instead of a scan
        # loop churning silently forever.
        await asyncio.sleep(2)
        if self._proc.returncode is not None:
            stderr = (await self._proc.stderr.read()).decode(errors="replace")
            logger.info(f"rtl_433 exited immediately (no RTL-SDR plugged in?): {stderr.strip()[-300:]}")
            self._proc = None
            return False
        logger.info(f"Sub-GHz (rtl_433) discovery started on {', '.join(freqs)}")
        asyncio.create_task(self._drain_stderr())
        return True

    async def _drain_stderr(self) -> None:
        """rtl_433 logs tuning/hop messages to stderr -- read and discard so
        its pipe never fills and blocks the process, but keep at debug
        level since none of it is actionable for an operator."""
        if not self._proc or not self._proc.stderr:
            return
        try:
            async for line in self._proc.stderr:
                logger.debug(f"rtl_433: {line.decode(errors='replace').rstrip()}")
        except Exception:
            pass

    async def scan(self) -> list[Rtl433Device]:
        """One batch of whatever decoded lines are available right now
        (non-blocking beyond a short read timeout) -- the daemon's own loop
        controls the cadence, this just drains what has arrived."""
        if not self._proc or not self._proc.stdout:
            return []
        out = []
        while True:
            try:
                line = await asyncio.wait_for(self._proc.stdout.readline(), timeout=0.2)
            except asyncio.TimeoutError:
                break
            if not line:
                break  # process ended
            try:
                data = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            key = _device_key(data)
            if not key:
                continue
            model = data.get("model", "RF device")
            out.append(Rtl433Device(
                key=key,
                label=model,
                model=model,
                rssi=data.get("rssi"),
                raw=meter_safe(data),
            ))
        return out

    async def stop(self) -> None:
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._proc.kill()
        self._proc = None
