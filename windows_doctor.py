# source: ai; ai_generated: (C)
"""Read-only Windows prerequisites. Never starts WDA or an app session."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent


def command(*args: str) -> str:
    environment = os.environ.copy()
    environment['APPIUM_HOME'] = str(ROOT / '.appium')
    # The device-list script reports its count through the shared info logger.
    # Capture it privately; check() exposes only fixed, redacted status messages.
    environment['APPIUM_IOS_REMOTEXPC_LOG_LEVEL'] = 'info'
    result = subprocess.run(
        [str(ROOT / '.tools/node_modules/.bin/appium.cmd'), *args],
        cwd=ROOT, env=environment, capture_output=True, text=True,
        encoding='utf-8', errors='replace', timeout=35,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    if result.returncode:
        raise RuntimeError('Lokal Appium-kommando fejlede.')
    return result.stdout + '\n' + result.stderr


def driver_version() -> str:
    try:
        drivers = json.loads(command('driver', 'list', '--installed', '--json'))
        driver = drivers.get('xcuitest') if isinstance(drivers, dict) else None
        version = driver.get('version') if isinstance(driver, dict) else None
        return version if isinstance(version, str) else ''
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired):
        return ''


def driver_installed() -> bool:
    return bool(driver_version())


def check(*, software_only: bool = False) -> dict:
    checks = []
    try:
        version = command('--version').strip()
        available = bool(re.fullmatch(r'3\.\d+\.\d+', version))
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        available = False
    checks.append(dict(key='appium', ok=available,
                       message='Appium 3 installeret.' if available else
                       'Appium 3 mangler eller kan ikke starte. Kør setup-windows.cmd.'))
    driver = driver_version() if available else ''
    supported = re.fullmatch(r'12\.(\d+)\.\d+', driver)
    installed = bool(supported and int(supported[1]) >= 20)
    checks.append(dict(key='xcuitest', ok=installed,
                       message='XCUITest-driver installeret.' if installed else
                       'Windows kræver XCUITest 12.20.0 eller nyere 12.x. Driveren mangler, '
                       'er inkompatibel eller kunne ikke kontrolleres. Se docs/WINDOWS.md.'))
    if installed and not software_only:
        try:
            output = command('driver', 'run', '--json', 'xcuitest', 'list-real-devices',
                             '--', '--connection', 'wired')
            payload = json.loads(output)
            lines = payload.get('output') if isinstance(payload, dict) else None
            count = re.search(r'\b(\d+) unique devices?\b', json.dumps(lines)) if isinstance(lines, list) else None
            usb = bool(count and int(count[1]) > 0)
            message = ('iPhone registreret via Apples USB-tjeneste.' if usb else
                       'Ingen bekræftet iPhone via USB. Lås telefonen op, godkend computeren, '
                       'og kontrollér datakablet og Apple Mobile Device Support.')
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired):
            usb = False
            message = ('USB-forbindelsen kunne ikke kontrolleres. Kontrollér Apple Mobile '
                       'Device Support, tilslut telefonen, og godkend computeren på iPhone.')
        checks.append(dict(key='usb', ok=usb, message=message))
    return dict(ok=all(item['ok'] for item in checks), checks=checks,
                device_ready=False,
                note='WDA-signering, iOS-version og aktiv RemoteXPC-tunnel er ikke verificeret. '
                     'Ingen telefonsession er startet. Se docs/WINDOWS.md.')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--software-only', action='store_true')
    parser.add_argument('--driver-installed', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if args.driver_installed:
        return 0 if driver_installed() else 1
    result = check(software_only=args.software_only)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        for item in result['checks']:
            print(('OK: ' if item['ok'] else 'MANGLER: ') + item['message'])
        print(result['note'])
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
