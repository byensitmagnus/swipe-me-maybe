# Contributing

Welcome. Bring small pull requests, reproducible bugs and a healthy suspicion
of claims that software can fix somebody's dating life.

## Start small

Fork the repository and create a short-lived branch. Run the offline demo
before changing anything. [The handoff](docs/HANDOFF.md) explains the architecture;
[the roadmap](docs/ROADMAP.md) contains useful first contributions.

The Python runtime uses the standard library only. Appium, XCUITest, WDA
and optional browser-test tooling are separate development prerequisites.
Keep new dependencies and abstractions justified by an actual failure.

```bash
python -m unittest discover -s tests -v
python -m py_compile app.py core.py bridge.py demo.py windows_doctor.py prepare_wda.py
node --check dashboard.js
```

On Windows, `py -3` can replace `python`. CI runs the synthetic suite on Windows
and Linux. No Apple credentials, phone connection or actual Hinge activity belong in CI.

For optional browser acceptance, install Playwright in a disposable environment,
provide its Chromium browser, then run `python tests/browser_smoke.py`.
`PLAYWRIGHT_CHROMIUM_EXECUTABLE` can point at an existing Chromium;
`BROWSER_SMOKE_OUTPUT` selects where synthetic screenshots are written.

## What a good pull request includes

- The concrete problem and resulting behavior.
- A focused regression test for meaningful behavior changes.
- The checks you ran, with synthetic-device evidence.
- Documentation for changed setup or platform requirements.
- A clear distinction between attempted actions and verified outcomes.

Keep conservative stop behavior, explicit live start, loopback bindings,
validation and uncertain-send handling intact. Do not introduce messages,
purchases, scraping, private service APIs, limit bypass or evasion.

## Real-device work

The owner signs and installs WDA locally, uses their own device and calibrates
actual controls. Start with preview. Any real attempt must be explicitly
started by the owner in the dashboard, separate from installation and tests.

Report platform/app versions and a minimal synthetic reproduction. Do not
upload real profile content, accessibility XML, device identifiers, screenshots,
device logs, signing material, account details or `.local/` files.
If an accessibility label contains personal information, replace it with
synthetic text before turning it into a fixture.

## License

Submit only work you have the right to contribute. Contributions are provided
under the repository's [MIT license](LICENSE). External dependencies retain
their own terms; see [NOTICE.md](NOTICE.md).
