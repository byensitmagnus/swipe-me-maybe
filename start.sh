#!/usr/bin/env bash
# source: ai; ai_generated: (C)
set -euo pipefail
cd "$(dirname "$0")"
python3 -c 'import sys; assert sys.version_info >= (3,11), "Installer Python 3.11+"'
if [[ "${1:-}" == '--demo' ]]; then
  shift
  exec python3 app.py --demo "$@"
fi
[[ "$(uname -s)" == Darwin ]] || { echo 'Den rigtige iPhone-driver kræver macOS. Brug --demo her.'; exit 1; }
export APPIUM_HOME="$PWD/.appium"
APPIUM="$PWD/.tools/node_modules/.bin/appium"
[[ -x "$APPIUM" ]] || { echo 'Kør bash setup-mac.sh først.'; exit 1; }
# Refuse an occupied port instead of commandeering another Appium session.
python3 - <<'PY'
import socket
for port in (4723, 8765):
    with socket.socket() as sock:
        try:
            sock.bind(('127.0.0.1', port))
        except OSError:
            raise SystemExit(f'Port {port} er optaget. Luk den eksisterende lokale server først.')
PY
"$APPIUM" --address 127.0.0.1 --port 4723 --log-level warn &
DRIVER_PID=$!
cleanup() { kill "$DRIVER_PID" 2>/dev/null || true; wait "$DRIVER_PID" 2>/dev/null || true; }
trap cleanup EXIT
python3 - <<'PY'
import json, time, urllib.request
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
for _ in range(60):
    try:
        with opener.open('http://127.0.0.1:4723/status', timeout=1) as response:
            data = json.load(response)
        if data.get('value', {}).get('ready') is True:
            break
    except (OSError, ValueError):
        pass
    time.sleep(.5)
else:
    raise SystemExit('Appium startede ikke. Se fejlen i denne Terminal.')
PY
python3 app.py "$@"
