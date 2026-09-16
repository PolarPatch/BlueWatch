# Credits

BlueWatch started from [bluehood](https://github.com/dannymcc/bluehood) by
Danny McClelland, MIT licensed. The Bluetooth/BLE scanning engine
(`bleak`-based scan loop), the SQLite persistence layer, the aiohttp web
server skeleton, and the ntfy.sh notification integration all trace back to
that project's original work.

BlueWatch has since diverged into its own project with a different device
categorization model (known/unknown triage, user-defined nested categories,
drag-and-drop assignment), a different per-device notification model
(independent arrive/depart toggles with temporary overrides), and an
independent watchlist mechanism — see `SPEC.md` for the full design. It is
not a GitHub fork of bluehood and carries no upstream tracking relationship,
by deliberate choice, but the debt to the original project's engineering is
worth naming plainly.

The original MIT license text (Danny McClelland, 2026) is preserved in
`LICENSE` as required by its terms.

## Third-party code

`bluewatch/rpa.py` (BLE Resolvable Private Address resolution against a
supplied Identity Resolving Key) is adapted from
[btrpa-scan](https://github.com/HackingDave/btrpa-scan) by David Kennedy /
TrustedSec, Apache License 2.0. The Apache-2.0 license text is preserved in
`THIRD_PARTY_LICENSE_btrpa-scan_Apache-2.0.txt` as required by its terms.

## Third-party data

`bluewatch/data/fastpair_model_ids.csv` (the Google Fast Pair Model ID
registry used for passive device identification in `classify_device()`)
is from the [WhisperPair](https://github.com/KULeuven-COSIC/WhisperPair)
research project (KU Leuven COSIC), licensed
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Several BLE fingerprints in `bluewatch/classifier.py` (Flipper Zero's
extra service UUIDs, Tesla's key-fob iBeacon UUID and iOS-fallback
advert, Lime/Swapfiets, Aruba access points, various vendor company
IDs, GAP Appearance category mapping, the Samsung TV/appliance
power-state decoder, and the Fast Pair Battery Notification decoder)
were identified by researching or cross-referencing
[blesploit/device-library](https://github.com/blesploit/device-library)
(MIT licensed) and its author Slawomir Jasek's published research
(notably the DEF CON 34 talk on BLESploit) -- reimplemented in
BlueWatch's own code style and data structures rather than copied
wholesale.

The Apple Continuity BLE decoders (`identify_apple_model()` and
`decode_apple_activity()` in `bluewatch/classifier.py` -- device model
identification and live screen/idle/call activity state) were
cross-verified against
[furiousMAC/continuity](https://github.com/furiousMAC/continuity)
(Naval Postgraduate School) and the academic paper "Handoff All Your
Privacy" (Celosia & Cunche, PoPETS 2019), reimplemented independently
from the documented protocol facts.
