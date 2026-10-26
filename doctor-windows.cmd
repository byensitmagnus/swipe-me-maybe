@echo off
setlocal
cd /d "%~dp0"
py -3 windows_doctor.py %*
exit /b %errorlevel%
