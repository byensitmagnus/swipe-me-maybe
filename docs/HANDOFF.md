# Matti, start here

The original local implementation task is being handed over as a public
experiment. The repository stays open for contributions. Nobody is claiming
that the physical Hinge integration is finished.

## First useful ten minutes

Run `py -3 app.py --demo` on Windows, or `python3 app.py --demo` elsewhere.
Preview a synthetic screen, try one attempt and inspect the counters.
Then run `python -m unittest discover -s tests -v`.
No phone or Apple login is needed for these steps.

Read `core.py` first, then `bridge.py`, then `app.py` and `dashboard.js`.
The runner knows exact calibrated button layouts, not what a profile means.

## What's done

The local UI, preview/start/stop, calibration API, bounded runner, Appium
transport, Windows doctor and unsigned IPA packer are implemented. Synthetic
browser acceptance covered preview, two cycles, calibration, stop and mobile
width. The [verification record](../VERIFICATION.md) separates measured evidence
from work that has never run on the actual app.

## The outstanding chain

1. **Sign and install WDA.** Use your own Apple signing setup. The project
   can prepare an unsigned IPA; it cannot issue an Apple certificate.
   See [Windows signing](WINDOWS-SIGNING.md) or [Mac setup](MAC-SETUP.md).
2. **Verify the tunnel and driver connection.** Windows uses iOS 18+,
   project-local Appium/XCUITest and RemoteXPC. See [Windows setup](WINDOWS.md).
3. **Calibrate the real controls locally.** Observe your own app's actual
   accessibility labels. Never invent selectors or submit profile content.
4. **Perform one owner-started acceptance attempt.** Preview first. Observe
   what happened and confirm stop/error behavior; a next-profile counter does
   not establish server acceptance.

The first three steps do not authorize an automatic live run. Device setup
and app actions remain separate. A successful demo cannot validate this chain.

## Exact bundle IDs on Windows

Some signing tools produce a full bundle ID that should be used verbatim.
The bridge supports private `device.local.json` configuration with
`"wda_bundle_id_exact": true`. This sets `updatedWDABundleIdSuffix` to an empty
string, instead of Appium's default `.xctrunner` suffix.

Use only the identifier actually installed on your own phone. The local API
accepts the flag, and preserves it for the same phone/ID when the form omits it.
The dashboard does not yet offer an explicit exact-ID control; see the roadmap.
Older base-ID configurations and the Mac path retain their behavior.

## Current limitations worth knowing

- The dashboard is in Danish; the public README and handoff are in English.
- App layout changes or unstable/dynamic button names may require adaptation.
- The Mac setup script is a retained alternative, not a tested signing path
  from the current Windows verification environment.
- Windows uses pinned Appium 3.8.0 and XCUITest 12.20.0; changing versions needs
  targeted compatibility checks, not just an npm upgrade.
- Third-party signing software and WDA are not bundled or covered by this MIT license.

## Working with other people

Fork and open a PR; the public repository does not require a collaborator
invitation for that. No private account setup, device identifiers or local
installation caches belong in the handoff. Start with [CONTRIBUTING.md](../CONTRIBUTING.md).
