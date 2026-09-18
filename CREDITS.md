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

Vehicle OEM phone-as-key/infotainment company IDs (Ford, Honda,
Hyundai, Toyota, Nissan, Subaru, BMW, Volkswagen, Porsche, Jaguar Land
Rover, and BYD, plus BLE-based TPMS tire sensors from Goodyear,
Schrader, and Pacific Industrial) in `bluewatch/classifier.py` were
identified from [OffGridPete/Fieldwatch](https://github.com/OffGridPete/Fieldwatch)
(MIT licensed, an Android BLE/WiFi signal-identification app formerly
named Spectre-APK), specifically its `DefaultCatalog.kt` fleet
definitions -- every company ID ported was independently
cross-verified against the Bluetooth SIG's own registry (see above)
before being trusted; one entry from that catalog ("Huf" tire/access
sensors) was left out because its claimed company ID does not appear
in the current SIG registry snapshot at all, and another (FOBO's
tire-pressure sensor) is matched by advertised name only rather than
its catalog company ID, since that ID resolves in the SIG registry to
a shared chipset supplier (Salutica Allied Solutions) rather than FOBO
itself.

The new Smart Lock type (`TYPE_LOCK` in `bluewatch/classifier.py`,
ASSA ABLOY/HID Global/Yale/SALTO/August/Allegion-Schlage company IDs),
Flipper Zero's second, independent MAC-OUI signal (`0C:FA:22`), the
UniFi Protect BLE setup-mode name pattern, and the cheap-BLE-serial-
module skimmer patterns (HM-10, JDY-08/10/16/31, BT05, etc.) were also
identified from OffGridPete/Fieldwatch's `DefaultCatalog.kt` -- the
smart-lock company IDs were independently cross-verified against the
Bluetooth SIG registry (all exact matches) and Flipper's OUI against
IEEE's own MA-L registry and Wireshark's manuf database before being
trusted. Fieldwatch's own bare `"ESP32"`/`"ESP32-*"` rule was
deliberately left out of the skimmer patterns -- it's the default
advertised name on countless unrelated hobbyist ESP32 projects, far
too generic to flag without a high false-positive rate.

DJI's model-aware drone/camera routing (`COMPANY_ID_DJI`,
`classify_dji_manufacturer_data()` in `bluewatch/classifier.py`) and
the Skydio/Autel/HOVERAir/Parrot BLE setup-mode name patterns were
identified from OffGridPete/Fieldwatch's `CatalogDecodes.kt` and
`DefaultCatalog.kt` (MIT licensed) -- DJI's company ID (0x08AA)
independently cross-verified against the Bluetooth SIG registry
(exact match: "SZ DJI TECHNOLOGY CO.,LTD"). DJI's own model-ID field
covers both its drones and its Osmo handheld/action-camera line under
the identical company ID and byte layout, so the decoded model ID is
routed to Drone or Camera accordingly rather than assuming every
0x08AA advert is a drone. These signatures are deliberately
complementary to (not redundant with) the ASTM F3411/OpenDroneID
Remote ID decoder added earlier the same night: per Fieldwatch's own
notes, these makers' in-flight Remote ID telemetry is "often Wi-Fi and
easy to miss" over BLE, so the setup/pairing-mode name patterns here
catch a separate, complementary signal.

Nuki smart lock/opener detection (`TYPE_LOCK` entries in
`SERVICE_UUID_PATTERNS`, `bluewatch/classifier.py`) uses the four
128-bit "Keyturner" service UUIDs (pairing and main-service, for both
the Lock and Opener product lines) read directly from
[technyon/nuki_ble](https://github.com/technyon/nuki_ble) (MIT
licensed), the official open-source Nuki BLE client library --
verified in its own `NukiLockConstants.h`/`NukiOpenerConstants.h`
source and confirmed via `NukiBle.cpp` that the pairing-service UUID
is read out of advertised BLE service data, a real signal available to
a passive scanner. Fieldwatch's `DefaultCatalog.kt` was what first
flagged that Nuki has a real UUID-based signature worth having, but
its actual UUID values weren't captured there; the values used here
come from Nuki's own reference implementation instead.

A second batch of smart-lock/smart-home/vehicle-tracker company IDs
in `bluewatch/classifier.py` (Tedee, igloohome, Master Lock, Kevo/
Unikey, dormakaba, Paxton/Net2 -> `TYPE_LOCK`; Chamberlain/myQ and
Hatch Baby -> `TYPE_SMART_HOME`; Samsara fleet telematics ->
`TYPE_VEHICLE`) plus name-only patterns (Chipolo/Pebblebee/"moto tag"
-> `TYPE_TRACKER`, Lockly/Kwikset -> `TYPE_LOCK`, Helium -> `TYPE_MESH`,
Fieldy/Plaud Note/NotePin recording wearables -> `TYPE_WEARABLE`) were
identified from OffGridPete/Fieldwatch's `DefaultCatalog.kt` (MIT
licensed) in a second research pass. Every company ID was
independently cross-verified against the Bluetooth SIG's own registry
before being trusted -- all ten resolved to an exact, specific vendor
match with no shared-chipset ambiguity.

Additional smart-glasses company IDs (`TYPE_GLASSES` in
`classify_by_manufacturer_data()`/`classify_device()`,
`bluewatch/classifier.py`: Luxottica Group and Snapchat Inc added bare
company-ID, matching the existing dedicated-glasses-maker tier; Sony,
Epson, and TCL added as company-ID-plus-name combinations since those
three are multi-product companies whose bare company ID would
misclassify their unrelated headphones/printers/phones as glasses)
were identified from
[BenGeorgie55/BLE-Scanner](https://github.com/BenGeorgie55/BLE-Scanner)
(AGPLv3 -- only the company-ID *values* were taken and independently
verified against the Bluetooth SIG's own registry, not any of its
code or rule-table structure, to stay clear of its copyleft/network-
disclosure terms). That same repo's camera/microphone/recording-device
rules were checked and found to be name-substring-only with no
company-ID/OUI/UUID backing at all -- no stronger than BlueWatch's
existing camera signal, so nothing from that part of it was adopted.
