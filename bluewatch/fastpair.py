"""Google Fast Pair anti-spoof verification ("Scan Unit" quick-action).

The Fast Pair "Key-based Pairing" handshake doubles as a genuine proof of
authenticity: only a device holding the correct per-model Anti-Spoofing
*Private* Key (kept secret on the chip, never broadcast) can produce a
reply that decrypts correctly to a Seeker that encrypted its challenge
with the matching *Public* Key. A cloned/spoofed advertisement (which only
copies what's visible over the air -- the Model ID, name, RSSI, etc.) has
no way to pass this challenge. This module implements that handshake from
the Seeker side, purely to answer "is the device broadcasting this Model
ID actually a genuine one" -- it does not complete pairing, bond, or write
an Account Key.

Protocol reference (verified against Google's own spec, not guessed):
https://developers.google.com/nearby/fast-pair/specifications/characteristics
https://developers.google.com/nearby/fast-pair/specifications/service/gatt
  - Key-based Pairing characteristic: ECDH on secp256r1 between an
    ephemeral Seeker keypair and the Provider's Anti-Spoofing Public Key;
    AES-128 key = first 16 bytes of SHA-256(shared secret); the 16-byte
    request/response blocks are single-block AES-ECB (no IV needed).
  - Request layout (16 bytes): type(1)=0x00, flags(1)=0x00 (no bonding
    request), provider address(6), padding/seeker address(6, unused here
    since the bonding-request flag is unset), random salt(2).

Anti-Spoofing Public Key lookup: this is deliberately NOT wired to any
network lookup by default. There is no documented self-service public API
for this -- Android's own Fast Pair implementation reaches it through a
private, Play-Services-only gRPC endpoint gated by an internal API key
(see the KULeuven-COSIC/WhisperPair academic research repo's
toolkit-server/src/model-id-resolver/index.ts for how that reverse-
engineered path works), which is a different trust/ToS situation than a
documented public API and isn't something to silently embed here.
Instead, resolve_anti_spoofing_key() reads a local, operator-maintained
JSON file (config.FASTPAIR_KEYS_PATH) mapping Model ID -> public key --
populate it by hand from whatever legitimate source you have (a vendor's
own docs, a device you registered yourself, etc.) for verification to
actually succeed; without an entry, verification cleanly reports
"no key available" rather than guessing or calling out to anything.
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import struct
from typing import Optional

from bleak import BleakClient
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from . import config
from .active_scan import SCAN_IN_PROGRESS
from .fastpair_models import model_id_from_service_data, lookup_fastpair_model  # noqa: F401 (model_id_from_service_data re-exported)

logger = logging.getLogger(__name__)

FASTPAIR_SERVICE_UUID = "0000fe2c-0000-1000-8000-00805f9b34fb"
MODEL_ID_CHAR_UUID = "fe2c1233-8366-4814-8eb0-01de32100bea"
KEY_BASED_PAIRING_CHAR_UUID = "fe2c1234-8366-4814-8eb0-01de32100bea"

VERIFY_TIMEOUT = 12.0
NOTIFY_WAIT_TIMEOUT = 5.0
MODEL_ID_READ_TIMEOUT = 12.0
_INPROGRESS_RETRIES = 4
_INPROGRESS_RETRY_DELAY = 3.0


async def read_fastpair_model_id(mac: str, adapter: Optional[str] = None) -> Optional[dict]:
    """Connect to a BLE device and read its Fast Pair Model ID directly off
    the GATT Model ID characteristic (fe2c1233-...) -- a plain, documented,
    unauthenticated read (no pairing, no crypto challenge, unrelated to
    verify_fastpair_device() above). This resolves devices whose Model ID
    isn't visible passively: once a Fast Pair accessory is already paired
    to its owner's phone, Google's spec has it switch to a "non-
    discoverable" advertising mode that drops the Model ID from
    service_data, even though the device still exposes the Fast Pair
    service and this characteristic over GATT.

    Returns the same shape as fastpair_models.identify_fastpair_device()
    (plus "model_id"), or None if the device doesn't have the Fast Pair
    service/characteristic, the read fails, or the Model ID isn't in the
    bundled registry. Never raises -- this is a best-effort enrichment
    step, not a required one.
    """
    kwargs = {"timeout": MODEL_ID_READ_TIMEOUT}
    if adapter:
        kwargs["adapter"] = adapter

    SCAN_IN_PROGRESS.set()
    try:
        for attempt in range(1, _INPROGRESS_RETRIES + 1):
            try:
                async with BleakClient(mac, **kwargs) as client:
                    char = client.services.get_characteristic(MODEL_ID_CHAR_UUID)
                    if not char or "read" not in char.properties:
                        return None
                    value = await client.read_gatt_char(char)
                    if len(value) != 3:
                        return None
                    model_id_hex = value.hex()
                    match = lookup_fastpair_model(model_id_hex)
                    if not match:
                        return None
                    return {**match, "model_id": model_id_hex}
            except asyncio.TimeoutError:
                return None
            except Exception as e:
                if "InProgress" in str(e) and attempt < _INPROGRESS_RETRIES:
                    logger.info(f"Fast Pair Model ID read: adapter busy (attempt {attempt}/{_INPROGRESS_RETRIES}), retrying in {_INPROGRESS_RETRY_DELAY}s")
                    await asyncio.sleep(_INPROGRESS_RETRY_DELAY)
                    continue
                logger.debug(f"Fast Pair Model ID read failed for {mac}: {e}")
                return None
        return None
    finally:
        SCAN_IN_PROGRESS.clear()


def resolve_anti_spoofing_key(model_id_hex: str) -> Optional[bytes]:
    """Look up a Model ID's 64-byte Anti-Spoofing Public Key from the local
    operator-maintained key store (see module docstring). Returns None if
    the file doesn't exist or has no entry for this Model ID."""
    path = config.FASTPAIR_KEYS_PATH
    if not path.exists():
        return None
    try:
        with open(path) as f:
            keys = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Could not read Fast Pair key store {path}: {e}")
        return None

    entry = keys.get(model_id_hex.lower()) or keys.get(model_id_hex.upper())
    if not entry:
        return None
    try:
        # Accept either hex or base64 -- whichever the operator pasted in.
        if all(c in "0123456789abcdefABCDEF" for c in entry):
            key = bytes.fromhex(entry)
        else:
            key = base64.b64decode(entry)
    except (ValueError, base64.binascii.Error) as e:
        logger.warning(f"Malformed Fast Pair key for model {model_id_hex}: {e}")
        return None

    if len(key) != 64:
        logger.warning(f"Fast Pair key for model {model_id_hex} is {len(key)} bytes, expected 64")
        return None
    return key


def _derive_aes_key(shared_secret: bytes) -> bytes:
    """AES-128 key = first 16 bytes of SHA-256(ECDH shared secret)."""
    digest = hashlib.sha256(shared_secret).digest()
    return digest[:16]


# ECB is protocol-mandated here, not a weaker choice we made: Google's own
# spec calls for exactly one 16-byte AES block with "no IV or multi-block
# cipher mode necessary" (see module docstring for the source). ECB's usual
# weakness -- identical plaintext blocks producing identical ciphertext --
# isn't a real concern for a single, freshly-randomized 16-byte block.
def _aes_ecb_encrypt_block(key: bytes, block: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.ECB())
    encryptor = cipher.encryptor()
    return encryptor.update(block) + encryptor.finalize()


def _aes_ecb_decrypt_block(key: bytes, block: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.ECB())
    decryptor = cipher.decryptor()
    return decryptor.update(block) + decryptor.finalize()


def _mac_to_bytes(mac: str) -> bytes:
    return bytes(int(b, 16) for b in mac.split(":"))


def _build_request(provider_mac: str) -> bytes:
    """16-byte Key-based Pairing request: type(1) + flags(1) +
    provider address(6) + padding(6) + salt(2). Flags=0x00: this is a
    verify-only probe, not a bonding request, so the seeker-address field
    (octets 8-13) is unused padding here rather than a real address."""
    msg_type = bytes([0x00])
    flags = bytes([0x00])
    provider_addr = _mac_to_bytes(provider_mac)
    padding = os.urandom(6)
    salt = os.urandom(2)
    request = msg_type + flags + provider_addr + padding + salt
    assert len(request) == 16
    return request


async def verify_fastpair_device(mac: str, model_id_hex: str, adapter: Optional[str] = None) -> dict:
    """Run the Fast Pair Key-based Pairing handshake against `mac` to check
    whether it holds the genuine Anti-Spoofing Private Key for `model_id_hex`.

    Returns a dict:
      {"ok": True, "verified": True/False, "model_id": ..., ...}
      {"ok": False, "error": "..."}  -- e.g. no key configured, connect
      failed, or the device doesn't expose the Key-based Pairing characteristic.
    """
    public_key = resolve_anti_spoofing_key(model_id_hex)
    if public_key is None:
        return {
            "ok": False,
            "error": (
                f"No Anti-Spoofing Public Key on file for Model ID {model_id_hex} "
                f"-- add one to {config.FASTPAIR_KEYS_PATH} to enable verification."
            ),
        }

    try:
        peer_public_numbers = ec.EllipticCurvePublicNumbers(
            x=int.from_bytes(public_key[:32], "big"),
            y=int.from_bytes(public_key[32:], "big"),
            curve=ec.SECP256R1(),
        )
        peer_public_key = peer_public_numbers.public_key()
    except ValueError as e:
        return {"ok": False, "error": f"Stored Anti-Spoofing Public Key for {model_id_hex} is invalid: {e}"}

    ephemeral_private_key = ec.generate_private_key(ec.SECP256R1())
    shared_secret = ephemeral_private_key.exchange(ec.ECDH(), peer_public_key)
    aes_key = _derive_aes_key(shared_secret)

    ephemeral_public_numbers = ephemeral_private_key.public_key().public_numbers()
    ephemeral_public_bytes = (
        ephemeral_public_numbers.x.to_bytes(32, "big") + ephemeral_public_numbers.y.to_bytes(32, "big")
    )

    request = _build_request(mac)
    encrypted_request = _aes_ecb_encrypt_block(aes_key, request)
    write_payload = encrypted_request + ephemeral_public_bytes  # 16 + 64 = 80 bytes

    kwargs = {"timeout": VERIFY_TIMEOUT}
    if adapter:
        kwargs["adapter"] = adapter

    SCAN_IN_PROGRESS.set()
    try:
        response_holder: dict = {}
        response_event = asyncio.Event()

        def _on_notify(_char, data: bytearray) -> None:
            response_holder["data"] = bytes(data)
            response_event.set()

        try:
            async with BleakClient(mac, **kwargs) as client:
                if not client.services.get_characteristic(KEY_BASED_PAIRING_CHAR_UUID):
                    return {"ok": False, "error": "Device does not expose the Fast Pair Key-based Pairing characteristic."}

                await client.start_notify(KEY_BASED_PAIRING_CHAR_UUID, _on_notify)
                try:
                    await client.write_gatt_char(KEY_BASED_PAIRING_CHAR_UUID, write_payload, response=True)
                    try:
                        await asyncio.wait_for(response_event.wait(), timeout=NOTIFY_WAIT_TIMEOUT)
                    except asyncio.TimeoutError:
                        return {
                            "ok": True,
                            "verified": False,
                            "model_id": model_id_hex,
                            "detail": "No response to the pairing challenge -- likely not the genuine device (or it requires pairing mode to be active).",
                        }
                finally:
                    try:
                        await client.stop_notify(KEY_BASED_PAIRING_CHAR_UUID)
                    except Exception:
                        pass

                response = response_holder.get("data", b"")
                if len(response) < 16:
                    return {
                        "ok": True,
                        "verified": False,
                        "model_id": model_id_hex,
                        "detail": f"Response too short ({len(response)} bytes) to be a valid encrypted reply.",
                    }

                decrypted = _aes_ecb_decrypt_block(aes_key, response[:16])
                # A genuine reply is type 0x01 (Key-based Pairing Response)
                # and echoes the Provider's own BLE address in octets 1-6 --
                # only decryptable/well-formed at all if the Provider used
                # the same shared secret, i.e. holds the matching private key.
                verified = decrypted[0] == 0x01
                provider_addr = ":".join(f"{b:02X}" for b in decrypted[1:7]) if verified else None

                return {
                    "ok": True,
                    "verified": verified,
                    "model_id": model_id_hex,
                    "provider_address": provider_addr,
                }
        except asyncio.TimeoutError:
            return {"ok": False, "error": "Timed out connecting -- device may be out of range or not connectable."}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    finally:
        SCAN_IN_PROGRESS.clear()


# model_id_from_service_data() now lives in fastpair_models.py (re-exported
# above) since it's also needed by classifier.py's passive Fast Pair Model
# ID lookup, which can't import this module (pulls in bleak/cryptography).
