# Verification record

## Public handoff — 2026-10-26

Fresh release checks are recorded here before publication. A passing synthetic
suite validates software behavior against fixtures, not compatibility with a
live version of Hinge.

| Check | Evidence |
| --- | --- |
| Python unit and HTTP integration suite | Passed on Windows, Python 3.14.3: 76 tests in 12.867s |
| Python compilation and JavaScript syntax | Passed: all six Python modules and dashboard.js |
| Headless browser acceptance with synthetic devices | Passed: preview, two cycles, calibration, stop, mobile width and zero JS exceptions |
| Public-source privacy and link checks | Passed on 58 staged files: no forbidden/private paths, credential patterns, personal machine paths/emails or missing local links |
| Independent source/publication review | APPROVE: exact 58-file staged candidate; privacy, licensing, docs, fixtures and workflow reviewed |
| GitHub Actions | Workflow provided; remote execution checked after push |
| Actual Hinge session | **Not verified** |

## Earlier measured software evidence — 2026-10-24

76 tests passed on Windows with Python 3.14.3. Node 24.15.0, Appium 3.8.0
and XCUITest 12.20.0 were used for local software setup. A real Appium server
returned ready, without creating a device session. The Windows setup was rerun
successfully and preserved its compatible driver installation.

Synthetic browser acceptance covered demo, preview without writes, two cycles,
manual calibration, stop, 390px width and zero JavaScript exceptions.
The published demo images are generated from the synthetic offline fixture.

A trusted USB connection and Developer Mode were observed on an iPhone.
No installed WDA runner was found. Public unsigned WDA was downloaded and
packaged locally; signing, installation, tunnel and real app acceptance did not
complete. No Apple credentials or physical profile data are distributed.

Independent review previously approved fixes to driver-version compatibility,
certificate-file rejection, Windows executable-path validation and exact WDA IDs.
The code must not turn those software results into a claim of live-app readiness.

## What would establish physical acceptance?

The device owner must sign/install WDA, verify the tunnel and Appium connection,
calibrate actual labels locally and explicitly start one supervised ordinary-like
attempt. Record app/platform versions and observed behavior without publishing
profiles, identifiers, XML or logs. A new-profile counter is not server acceptance.

See the [handoff](docs/HANDOFF.md) and [Windows guide](docs/WINDOWS.md).

A clean export of the staged source started the offline demo without .local,
Appium packages or installed drivers; zero device sessions. Bash setup/start
script syntax also passed. Only synthetic documentation screenshots were generated.
