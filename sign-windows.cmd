@echo off
setlocal
cd /d "%~dp0"
if not exist ".local\WebDriverAgent.ipa" (
  echo Run prepare-wda-windows.cmd first.
  pause
  exit /b 1
)
if not exist ".qa\sideloadly-portable\sideloadly.exe" (
  echo Download Sideloadly from https://sideloadly.io/ and open it.
  echo Load this IPA: %CD%\.local\WebDriverAgent.ipa
  start "" explorer.exe /select,"%CD%\.local\WebDriverAgent.ipa"
  pause
  exit /b 0
)
start "" explorer.exe /select,"%CD%\.local\WebDriverAgent.ipa"
start "" "%CD%\.qa\sideloadly-portable\sideloadly.exe"
