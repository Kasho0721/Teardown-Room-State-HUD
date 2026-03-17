@echo off
setlocal
cd /d %~dp0\..

python -m pip install --upgrade nuitka ordered-set zstandard >nul 2>nul

if exist build\nuitka rd /s /q build\nuitka
if exist dist\teardown-room-bridge-nuitka.dist rd /s /q dist\teardown-room-bridge-nuitka.dist
if exist dist\teardown-room-bridge-nuitka.exe del /f /q dist\teardown-room-bridge-nuitka.exe

python -m nuitka ^
  --standalone ^
  --assume-yes-for-downloads ^
  --output-dir=dist ^
  --remove-output ^
  --windows-console-mode=disable ^
  --follow-imports ^
  --include-package=agent ^
  --include-data-files=web\webui.html=webui.html ^
  --include-data-files=web\ui.html=ui.html ^
  --include-data-files=bridge_config.json=bridge_config.json ^
  --output-filename=teardown-room-bridge-nuitka.exe ^
  run_bridge.py

if errorlevel 1 (
  echo.
  echo Nuitka standalone build failed.
  exit /b 1
)

echo.
echo Build finished:
echo %cd%\dist\teardown-room-bridge-nuitka.dist\
