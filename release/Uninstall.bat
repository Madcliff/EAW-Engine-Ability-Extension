@echo off
rem Removes the ZZ_SWFOC engine patch and restores the stock exe import.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Uninstall %*
echo.
pause
