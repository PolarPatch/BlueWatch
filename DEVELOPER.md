# Developer log: known-but-unfound signatures

Running list of devices/vendors we know are worth fingerprinting but
haven't found concrete, verifiable protocol data (OUI, Bluetooth
company ID, service UUID, or byte-level manufacturer-data pattern) for
yet. Kept separate from CREDITS.md, which only documents data that's
actually been implemented.

**How to use this file**: when a research pass comes up empty for a
device/vendor the operator specifically wants, log it here instead of
dropping it silently. A future session (or a manual GitHub/web search)
can come back to any entry below. Move an entry to CREDITS.md (with
its source) once it's actually implemented, and delete the line here.

Each entry: what we're looking for, why it matters, what's been
checked already (so we don't repeat dead ends), and where to look next
(GitHub repos, vendor docs, protocol write-ups, teardown blogs, FCC ID
filings, etc.) -- both code repos and plain web pages/forum posts can
carry this kind of data, not just GitHub.

---

## Format

```
### <Vendor/device>
- **Why**: <what this would let BlueWatch detect, and why the operator cares>
- **Checked, no data found**: <repos/sources already searched this session, so we don't repeat them>
- **Next**: <where to look next -- specific repo names, search terms, doc types>
```

---

### Nuki smart locks (BLE)
- **Why**: Fieldwatch's `DefaultCatalog.kt` has a real Nuki rule (5 custom
  128-bit service UUIDs, `bleName`/`bleGlob`-backed) -- confirmed to exist,
  but the research pass that found it didn't extract the actual UUID
  values, and a quick follow-up check of `technyon/nuki_ble` and
  `technyon/nuki_hub` (both open-source Nuki BLE bridges) didn't turn up
  the UUIDs on a shallow README grep. Nuki is a very common European
  smart-lock brand, worth having.
- **Checked, no data found**: OffGridPete/Fieldwatch's `DefaultCatalog.kt`
  (UUIDs referenced but not captured), `technyon/nuki_ble` README,
  `technyon/nuki_hub` README (both shallow grep only, not a full read).
- **Next**: Do a full read (not just README grep) of `technyon/nuki_ble`'s
  source (likely a `.h`/`.cpp` or Python BLE-client file defining GATT
  service/characteristic UUIDs) -- this is the most likely place to find
  Nuki's real service UUID(s) since it's a working open-source
  implementation, not just documentation. Also check Nuki's own public API
  docs (developer.nuki.io) and the Fieldwatch `DefaultCatalog.kt` file
  directly again with a targeted search for "nuki" (case-insensitive) to
  pull the exact 5 UUIDs Fieldwatch uses.

### Camera/ALPR brands: name-pattern-only, no OUI/UUID/company-ID backing
- **Why**: User specifically asked about wireless camera detection.
  Hikvision, Dahua, Genetec AutoVu, Rekor, Avigilon, Axis, Verkada,
  Motorola Vigilant, Penguin, Pigvision are all primarily wired/PoE
  security cameras -- Fieldwatch only matches them by advertised
  name/SSID (`name()`/`glob()`, no `radio=` qualifier, so it's actually
  ambiguous whether Fieldwatch's own rule fires on BLE, WiFi, or both).
  BLE only shows up on these at all during initial setup/pairing, so a
  name-only match is a much weaker signal than the OUI/company-ID/UUID
  fingerprints elsewhere in BlueWatch's classifier.
- **Checked, no data found**: OffGridPete/Fieldwatch's `DefaultCatalog.kt`
  -- confirmed these have no OUI/UUID/company-ID rules, name-pattern only.
  Deliberately not ported this round (per operator decision to implement
  "strong findings only" first) -- exact name strings ARE known (see the
  research fork's report, preserved in this session's history) if the
  operator wants to add them later as low-confidence patterns.
- **Next**: If wanted, these can be added directly from the already-known
  name strings (Hikvision/HIKVISION, Dahua/DAHUA, Genetec/AutoVu,
  Rekor, Avigilon, AXIS-*/Axis-*, Verkada, "Vigilant Solutions"/"Motorola
  Vigilant", Penguin/PIGVISION) as name-pattern matches -- no further
  research needed, just an implementation decision. For a STRONGER
  signal than name-only, search for each vendor's own BLE SDK/app source
  on GitHub (e.g. "Axis Companion app" reverse-engineering write-ups,
  Hikvision's "Hik-Connect" BLE pairing protocol docs) -- vendor
  onboarding-app teardowns sometimes reveal a real manufacturer-data
  company ID or service UUID that a general-purpose scanner app like
  Fieldwatch wouldn't bother matching on.

### FS Ext Battery (Flock Safety pole battery pack) -- unverified OUIs
- **Why**: Part of the Flock Safety camera-pole ecosystem already
  partially covered (Flock's own OUI + name patterns are already in
  BlueWatch). This is the battery/power module, a different physical
  unit with its own BLE presence (likely for maintenance/status).
- **Checked, no data found**: Fieldwatch's `DefaultCatalog.kt` has 9 MAC
  OUIs for this (`04:0D:84, 1C:34:F1, 38:5B:44, 94:34:69, B4:E3:F9,
  F0:82:C0, 58:8E:81, EC:1B:BD, 90:35:EA`) plus name patterns
  (`FS Ext Battery`, `FS_*`, `FS Ext*`) -- extracted but NOT
  cross-verified against IEEE's OUI registry, and not implemented this
  round pending that verification.
- **Next**: Cross-check each of those 9 OUIs against
  `standards-oui.ieee.org/oui/oui.csv` (same method used to verify
  Flipper Zero's OUI this session) before trusting/implementing --
  several small/generic-looking OUI blocks in that list could easily be
  a shared component vendor (contract manufacturer) rather than
  something specific to Flock hardware, the same trap FOBO's company ID
  turned out to be for the vehicle-TPMS signatures.

### Google Fast Pair "Hide account-key noise" filter (UX idea, not new data)
- **Why**: Fieldwatch has a UI filter that hides already-paired Fast Pair
  accessories with no other identifying signature ("plaza noise" --
  crowds of strangers' earbuds broadcasting a generic account-key TLV).
  Confirmed this is NOT a new protocol-decode capability BlueWatch is
  missing (BlueWatch's Fast Pair pipeline -- passive Model ID resolution,
  active Model ID read fallback, battery decode, anti-spoof crypto
  verification -- is already more complete than what Fieldwatch
  documents). This is purely a dashboard noise-reduction idea.
- **Checked, no data found**: N/A -- this isn't a missing-data item, it's
  a pending UI-feature decision the operator hasn't confirmed yet.
- **Next**: If the operator wants this, it's a straightforward dashboard
  filter (hide devices where the only Fast Pair signal is a bare
  service-UUID 0xFE2C match with no resolved Model ID/name) -- no
  external research needed, just an implementation task.
