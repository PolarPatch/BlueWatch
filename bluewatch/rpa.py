"""Bluetooth LE Resolvable Private Address (RPA) resolution against IRKs.

Adapted from btrpa-scan (https://github.com/HackingDave/btrpa-scan) by
David Kennedy / TrustedSec, Apache License 2.0 -- see
THIRD_PARTY_LICENSE_btrpa-scan_Apache-2.0.txt at the repo root and
CREDITS.md. Only the resolution primitive is carried over; the rest of
that project (GUI, GPS stamping, TUI, distance estimation) is unrelated
to what's implemented here.

An Identity Resolving Key (IRK) lets you prove -- cryptographically, not
by guessing from an advertised name -- that a privacy-randomized MAC
address belongs to a specific device you already possess the key for
(typically extracted from your own phone's Bluetooth pairing data).
There is no way to resolve a randomized address for a device you don't
hold the IRK for, by design -- that's the whole point of BLE address
privacy.
"""

from typing import Optional

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


def parse_irk_hex(irk_string: str) -> bytes:
    """Parse an IRK from a hex string (plain, colon-separated, or 0x-prefixed).

    Returns 16 bytes or raises ValueError.
    """
    s = irk_string.strip()
    if s.lower().startswith("0x"):
        s = s[2:]
    s = s.replace(":", "").replace("-", "")
    if len(s) != 32:
        raise ValueError(f"IRK must be exactly 16 bytes (32 hex chars), got {len(s)} hex chars")
    return bytes.fromhex(s)


def _bt_ah(irk: bytes, prand: bytes) -> bytes:
    """Bluetooth Core Spec ah() function (Vol 3, Part H, Section 2.2.2).

    AES-128-ECB(IRK, padding || prand) -> return last 3 bytes.

    ECB mode is mandated by the Bluetooth Core Specification for this
    single-block operation -- only one 16-byte block is ever encrypted, so
    ECB's lack of diffusion across blocks is irrelevant here.
    """
    plaintext = b"\x00" * 13 + prand  # 16 bytes: 13 zero-pad + 3-byte prand
    cipher = Cipher(algorithms.AES(irk), modes.ECB())
    enc = cipher.encryptor()
    ct = enc.update(plaintext) + enc.finalize()
    return ct[-3:]


def _is_rpa(addr_bytes: bytes) -> bool:
    """A Resolvable Private Address has the top two bits of the MSB set to 01."""
    return len(addr_bytes) == 6 and (addr_bytes[0] >> 6) == 0b01


def resolve_rpa(irk: bytes, mac: str) -> bool:
    """Return True if the given MAC resolves against this IRK.

    mac format: AA:BB:CC:DD:EE:FF. prand = first 3 octets, hash = last 3
    octets; matches if ah(IRK, prand) == hash. Returns False for anything
    that isn't a well-formed RPA (fixed/public addresses never resolve).
    """
    if not HAS_CRYPTOGRAPHY:
        return False
    parts = mac.replace("-", ":").split(":")
    if len(parts) != 6:
        return False
    try:
        addr_bytes = bytes(int(b, 16) for b in parts)
    except ValueError:
        return False
    if not _is_rpa(addr_bytes):
        return False
    prand = addr_bytes[:3]
    expected_hash = addr_bytes[3:]
    return _bt_ah(irk, prand) == expected_hash


def resolve_against_keys(mac: str, irks: list[tuple[str, bytes]]) -> Optional[str]:
    """Try mac against a list of (label, irk_bytes) pairs; return the first
    matching label, or None if no key resolves it."""
    for label, irk in irks:
        if resolve_rpa(irk, mac):
            return label
    return None
