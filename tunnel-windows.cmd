@echo off
setlocal
cd /d "%~dp0"
set "APPIUM_HOME=%CD%\.appium"
if not exist ".tools\node_modules\.bin\appium.cmd" (
  echo Run setup-windows.cmd first.
  exit /b 1
)
echo RemoteXPC tunnel only. No Hinge session or likes are started.
echo Use an Administrator terminal if Windows denies tunnel creation.
call ".tools\node_modules\.bin\appium.cmd" driver run xcuitest tunnel-creation
