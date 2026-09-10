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

`bluehood/rpa.py` (BLE Resolvable Private Address resolution against a
supplied Identity Resolving Key) is adapted from
[btrpa-scan](https://github.com/HackingDave/btrpa-scan) by David Kennedy /
TrustedSec, Apache License 2.0. The Apache-2.0 license text is preserved in
`THIRD_PARTY_LICENSE_btrpa-scan_Apache-2.0.txt` as required by its terms.
