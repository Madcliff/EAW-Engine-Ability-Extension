@echo off
rem Installs the ZZ_SWFOC engine patch (EAW Engine Ability Extension). Double-click to run.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"  %*
echo.
pause
