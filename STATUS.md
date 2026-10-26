# Project status

Updated: 2026-10-26 · **Community handoff**

The original local implementation task is closed at this source handoff.
The open-source repository remains open for Matti and other contributors.
Physical Hinge acceptance is **unfinished**; this is an experimental release.

## Delivered

- Local dashboard, offline demo, preview, calibration and bounded start/stop.
- Appium/XCUITest bridge, Windows prerequisite doctor and unsigned WDA packer.
- Synthetic tests and Windows/Linux CI workflow.
- MIT license, original banner, contributor documentation and community templates.
- [Handoff](docs/HANDOFF.md) and [roadmap](docs/ROADMAP.md) for continuation.

## Remaining

Sign/install WDA → verify the RemoteXPC tunnel and device connection → calibrate
actual controls locally → perform one owner-started, supervised acceptance attempt.
No actual Hinge session or server-confirmed like has been demonstrated.

Personal account setup, private device state, local tool caches and signing
material are not part of the public project. No account or credential is supplied.
See [VERIFICATION.md](VERIFICATION.md) for evidence and its limits.
