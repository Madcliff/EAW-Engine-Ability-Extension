@echo off
rem Shows whether the ZZ_SWFOC engine patch is installed.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Status %*
echo.
pause
