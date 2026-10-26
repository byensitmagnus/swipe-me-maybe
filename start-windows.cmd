@echo off
setlocal
cd /d "%~dp0"
set "APPIUM_HOME=%CD%\.appium"
if not exist ".tools\node_modules\.bin\appium.cmd" (
  echo Run setup-windows.cmd first.
  exit /b 1
)
echo Keep this terminal open. Start panel-windows.cmd in another terminal.
call ".tools\node_modules\.bin\appium.cmd" --address 127.0.0.1 --port 4723 --log-level warn
