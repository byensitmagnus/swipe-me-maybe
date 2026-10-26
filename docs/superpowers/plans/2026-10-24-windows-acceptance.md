# Windows acceptance: historical implementation checklist

This records the completed software work behind the public v0.2 handoff.
Current continuation instructions are in ../../HANDOFF.md and ../../ROADMAP.md.

- [x] Preserve the stdlib runner, local dashboard and Mac connection path.
- [x] Install project-local Appium 3.8.0 and XCUITest 12.20.0 for Windows verification.
- [x] Replace the Windows doctor's erroneous Xcode requirement with platform checks.
- [x] Preserve installed drivers on repeated setup and gate compatibility.
- [x] Test browser demo, preview, calibration, stop and mobile layout with fixtures.
- [x] Prepare unsigned WDA packaging, reject signing material and unsafe executable paths.
- [x] Support exact observed WDA bundle IDs without changing legacy behavior.
- [x] Obtain independent review of the source changes.
- [ ] Sign/install WDA, verify a tunnel, calibrate real labels and complete owner-started physical acceptance.

No real Hinge session was run during implementation or software tests.
Private account setup and device-specific configuration are intentionally omitted.
