# BlueWatch - design spec (draft)

Bluetooth neighborhood-presence tool. Started as a fork-worthy evaluation of
[dannymcc/bluehood](https://github.com/dannymcc/bluehood) (MIT licensed -
free to reuse code/architecture, only obligation is keeping the MIT license
notice somewhere in the project if source is carried over; no requirement to
publish, open-source, or credit it as a fork in the product itself). Decision
as of 2026-09-09: build as its own project reusing bluehood's proven
plumbing (bleak BLE scan loop, aiosqlite schema/persistence pattern, aiohttp
web app skeleton, ntfy.sh notification sender) rather than a literal GitHub
fork. Not on GitHub yet, staying local until it's further along.

All product-facing naming stays in English per user's explicit instruction.

## Core model

**Top level split (mutually exclusive): Known vs. Unknown**
- **Unknown** - default landing pool for new/unrecognized devices. Notifies
  as normal (subject to global new-device settings) until triaged by the
  user into a Known category.
- **Known** - device has been assigned to a user-defined category.

**Known → user-defined top-level categories (siblings, fully custom names)**
Examples discussed (not hardcoded, user names these themselves):
- `Home` - own household devices
  - optional subgroups: IoT, Phones, Watches, Mesh (e.g. Meshtastic nodes)
- `Known Neighbours` - neighboring households' devices (e.g. a neighbor's
  robot lawnmower - mildly interesting once, then permanently uninteresting)
- `Friends & Acquaintances` - people who visit occasionally

Subgroups are optional per category. Assignment happens via **drag-and-drop**
from the "Identified Targets" list (bluehood's existing device table) into a
category/subgroup in the sidebar - much faster than a dropdown for
triaging a long list.

**Per-device detail panel** (opens on clicking/selecting a device row in
Identified Targets):
- Category / subgroup assignment
- **Watchlist** toggle - fully independent of category (a device can be
  both categorized AND watched). Enables presence statistics: frequency /
  pattern of appearance over time (daily rhythm etc.). bluehood already
  persists `first_seen` / `last_seen` / `total_sightings` per device, so the
  data layer mostly exists already - this mainly needs a stats view.
- **Arrive notification**: Off / On (Always) / On (24h temporary)
- **Depart notification**: Off / On (Always) / On (24h temporary)
  - Motivating example: temporarily enable Arrive-only on a kid's Apple
    Watch to get pinged when they get home from school, without wanting a
    permanent standing notification.
  - The 24h mode is a genuine temporary override - auto-expires back to Off
    (or back to whatever the category default was) after 24h elapses. Not
    yet decided: does it also auto-expire after firing once, or strictly by
    the 24h clock regardless of how many arrive/depart events fire in that
    window? **Leaning toward the 24h clock (not one-shot)**, since "notify
    me all afternoon when kids arrive" implies it should survive multiple
    events in that window - confirm before implementing.

**Default notification behavior**: Known/categorized devices are silent by
default (that's the whole point - cut noise from expected devices). Per-
device Arrive/Depart overrides win over the category default. Unknown
devices notify as normal until triaged.

## Known gotchas from the bluehood instance already running

(Reference only - not necessarily the base for BlueWatch's own codebase,
but useful signal from real-world data.)

- **69 of 77 detected devices use randomized/rotating MAC addresses.** This
  matters a lot for "new device" detection and for category assignment
  persistence - a randomized-MAC device will look like a brand-new device
  on every rotation unless BlueWatch (like bluehood attempts to) correlates
  rotations to the same physical device via other signals (service UUIDs,
  manufacturer data, advertised name, RSSI/timing correlation). Naively
  keying everything off MAC address alone will make categorization
  "stick" only until the next MAC rotation, then the device reappears in
  Unknown again and re-notifies - this was the literal complaint that led
  to disabling notifications during development (multiple pings per minute
  from rotating MACs re-triggering "new device").
- bluehood's `/api/settings` endpoint does a **full replace, not a partial
  merge** - POSTing `{"ntfy_enabled": false}` alone wiped `ntfy_topic` and
  `notify_new_device` back to blank/false as a side effect. Worth deciding
  deliberately for BlueWatch's own API: partial PATCH semantics are almost
  certainly less surprising and safer for a settings endpoint.
- bluehood's `device_groups` table (name/color/icon only) has **no
  notification-related column at all** - the desired "categorize into a
  quiet bucket" behav1or doesn't exist upstream, confirming this needs to be
  designed fresh rather than reused as-is. `ignored` is a per-device flag
  that hides devices from the dashboard but is *not* checked by the
  notification code path (`notifications.py: on_device_seen`) - another gap
  confirmed by reading the source directly.
