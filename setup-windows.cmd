@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 goto :python_error
node -e "const [a,b]=process.versions.node.split('.').map(Number);process.exit((a===20&&b>=19)||(a===22&&b>=12)||a>=24?0:1)"
if errorlevel 1 goto :node_error
call npm --version
if errorlevel 1 goto :node_error
set "APPIUM_HOME=%CD%\.appium"
call npm install --prefix .tools --save-exact --no-audit --no-fund appium@3.8.0
if errorlevel 1 exit /b 1
py -3 windows_doctor.py --driver-installed
if not errorlevel 1 goto :driver_ready
call ".tools\node_modules\.bin\appium.cmd" driver install xcuitest@12.20.0
if errorlevel 1 exit /b 1
:driver_ready
py -3 windows_doctor.py --software-only
if errorlevel 1 exit /b 1
echo Setup complete. Read docs\WINDOWS.md before connecting the phone.
exit /b 0
:python_error
echo Install Python 3.11 or newer with the Windows Python launcher.
exit /b 1
:node_error
echo Install Node.js 22.12+ or 24 LTS with npm 10+.
exit /b 1
