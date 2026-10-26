# Agent and contributor notes

This is a local, bounded iPhone UI-automation experiment. Read README.md,
STATUS.md and VERIFICATION.md before making readiness claims.

Keep changes in this standalone repository. Publication, push and live actions
require the owner's current mandate. The public handoff does not authorize
an agent to run real Hinge sessions on a contributor's phone.

Never inspect or upload private .local, .tools, .appium, .qa or cache content,
credentials, certificates, real UI XML, device logs or profile screenshots.
Use synthetic fixtures. The committed images in docs/assets are synthetic demo
artifacts or original artwork, not phone/profile screenshots.

Do not start live sessions while installing or running automated tests.
No messages, purchases, roses, private Hinge APIs, bypassing limits, CAPTCHA
handling or evasion. Preserve exact observed selectors and conservative stops.

Run from this folder:

    python -m unittest discover -s tests -v
    python -m py_compile app.py core.py bridge.py demo.py windows_doctor.py prepare_wda.py
    node --check dashboard.js

Python 3.11+ standard library only at runtime. Appium 3/XCUITest are external.
Windows requires iOS 18+, signed preinstalled WDA and an active RemoteXPC tunnel.
Tests with synthetic devices do not prove actual Hinge compatibility. Never
invent labels or blind coordinate clicks to fill an acceptance gap.

For continuation, read docs/HANDOFF.md and docs/ROADMAP.md.
