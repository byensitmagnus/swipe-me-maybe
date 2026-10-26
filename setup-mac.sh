#!/usr/bin/env bash
# source: ai; ai_generated: (C)
set -euo pipefail
cd "$(dirname "$0")"
[[ "$(uname -s)" == Darwin ]] || { echo 'iPhone-opsætningen kræver macOS. Demo: python3 app.py --demo'; exit 1; }
command -v python3 >/dev/null || { echo 'Installer Python 3.11+ først.'; exit 1; }
python3 -c 'import sys; assert sys.version_info >= (3,11), "Installer Python 3.11+"'
xcodebuild -version || { echo 'Installer hele Xcode, åbn det én gang og vælg det som aktivt udviklerværktøj.'; exit 1; }
command -v node >/dev/null || { echo 'Installer Node.js 22.12+ eller 24 LTS og npm 10+ først.'; exit 1; }
command -v npm >/dev/null || { echo 'Installer npm 10+ først.'; exit 1; }
node -e 'const [a,b]=process.versions.node.split(".").map(Number); if(!((a===20&&b>=19)||(a===22&&b>=12)||a>=24)){console.error("Appium 3 kræver Node 20.19+, 22.12+ eller 24+");process.exit(1)}'
[[ "$(npm --version | cut -d. -f1)" -ge 10 ]] || { echo 'Opdater til npm 10+ først.'; exit 1; }
export APPIUM_HOME="$PWD/.appium"
mkdir -p .tools
# Local installation only. npm saves the resolved version and package-lock.json.
if [[ ! -x .tools/node_modules/.bin/appium ]]; then
  npm install --prefix .tools --save-exact --no-audit --no-fund appium@3
fi
APPIUM="$PWD/.tools/node_modules/.bin/appium"
if ! "$APPIUM" driver list --installed --json | grep -q '"xcuitest"'; then
  "$APPIUM" driver install xcuitest
fi
"$APPIUM" driver doctor xcuitest
printf '\nDriver installeret. Næste trin:\n  bash open-wda.sh\nSignér WebDriverAgentRunner i Xcode til din iPhone. Se README.md.\nDerefter: bash start.sh\n'
