# Prototype architecture

The public v0.2 experiment retains the original Python runner and Mac path,
and adds a Windows connection using preinstalled WebDriverAgent.

- Python standard library: deterministic runner, Appium transport and local HTTP API.
- Browser UI: manual calibration, preview, explicit start and stop.
- Appium/XCUITest/WDA: external device-control prerequisites.
- Synthetic demo: isolated from real device sessions.

Windows startup is split into tunnel, Appium and panel commands so failures
remain visible. There is no private service API integration or coordinate guessing.

The source handoff is complete; physical Hinge compatibility is not verified.
Current status and next steps live in [the handoff](HANDOFF.md),
[roadmap](ROADMAP.md) and [verification record](../VERIFICATION.md).
