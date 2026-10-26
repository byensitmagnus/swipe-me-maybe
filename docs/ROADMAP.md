# Roadmap

The initial local implementation task is closed at source handoff. Community
development stays open. These are the useful next steps, in dependency order.

| Priority | Work | Acceptance |
| --- | --- | --- |
| P0 | [Signed WDA + tunnel + physical acceptance (#1)](https://github.com/byensitmagnus/swipe-me-maybe/issues/1) | Owner verifies the full connection and one explicitly started attempt; report versions and a synthetic reproduction, no personal data |
| P1 | [English dashboard (#2)](https://github.com/byensitmagnus/swipe-me-maybe/issues/2) | All visible copy translated consistently; demo, calibration, preview and stop still work |
| P1 | [Explicit Windows exact-bundle-ID setting (#3)](https://github.com/byensitmagnus/swipe-me-maybe/issues/3) | Choice is visible, saved and round-trips without altering legacy base-ID/Mac behavior |
| P2 | [Reproducible Mac dependency setup (#4)](https://github.com/byensitmagnus/swipe-me-maybe/issues/4) | Document/test compatible pinned versions without changing a working local signing installation |

## Already present

- Offline demo and synthetic unit/HTTP/browser tests.
- Bounded ordinary-like runner and stop/uncertain-send handling.
- Local-only dashboard and manual control calibration.
- Windows prerequisite doctor and unsigned WDA packaging.
- Open-source licensing, community templates and a contributor handoff.

## Outside the current scope

Messages, purchases, roses, profile ranking/archives, private Hinge APIs,
CAPTCHA handling, rate-limit bypass, stealth and unattended autonomous sessions.
The experiment makes no promise about matches or account safety.
