#!/usr/bin/env bash
# source: ai; ai_generated: (C)
set -euo pipefail
cd "$(dirname "$0")"
export APPIUM_HOME="$PWD/.appium"
[[ -x .tools/node_modules/.bin/appium ]] || { echo 'Kør bash setup-mac.sh først.'; exit 1; }
exec .tools/node_modules/.bin/appium driver run xcuitest open-wda
