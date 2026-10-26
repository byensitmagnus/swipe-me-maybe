@echo off
setlocal
cd /d "%~dp0"
set "APPIUM_HOME=%CD%\.appium"
if not exist ".tools\node_modules\.bin\appium.cmd" (
  echo Run setup-windows.cmd first.
  exit /b 1
)
if exist ".local\WebDriverAgent.ipa" (
  echo The local IPA already exists and will not be overwritten.
  exit /b 1
)
if exist ".local\wda-unsigned" goto :package
call ".tools\node_modules\.bin\appium.cmd" driver run xcuitest download-wda -- --platform=ios --kind=real "--outdir=%CD%\.local\wda-unsigned"
if errorlevel 1 exit /b 1
:package
py -3 prepare_wda.py ".local\wda-unsigned\WebDriverAgentRunner-Runner.app"
exit /b %errorlevel%
