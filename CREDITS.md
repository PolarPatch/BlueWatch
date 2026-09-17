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

`bluewatch/data/company_identifiers.csv` (used by
`bluewatch/company_identifiers.py` as a vendor-name fallback for devices
whose MAC address gives no real OUI to look up, e.g. a randomized
privacy address) is converted from the Bluetooth SIG's own public
[assigned-numbers registry](https://bitbucket.org/bluetooth-SIG/public/src/main/assigned_numbers/company_identifiers/company_identifiers.yaml),
the official source for BLE manufacturer company IDs.

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

Plejd smart-home device recognition (`classify_device()` in
`bluewatch/classifier.py`, matching the generic "P mesh" name every
Plejd BLE mesh device advertises) was identified by researching
[thomasloven/hass-plejd](https://github.com/thomasloven/hass-plejd)
and its underlying [pyplejd](https://github.com/thomasloven/pyplejd)
library (MIT licensed), including a live connection log in
[hass-plejd#147](https://github.com/thomasloven/hass-plejd/issues/147)
confirming the advertised name. Per-model identification (which
specific switch/dimmer/relay) was investigated but not implemented --
pyplejd resolves that from Plejd's cloud API tied to the owner's
account, and even its legacy local-lookup table required first
authenticating into the encrypted mesh, both out of scope for
BlueWatch's passive/unauthenticated identification model.
