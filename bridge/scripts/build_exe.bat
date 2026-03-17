@echo off
setlocal
cd /d %~dp0
python -m pip install --upgrade pyinstaller >nul 2>nul
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onedir ^
  --name teardown-room-bridge ^
  --hidden-import app ^
  --hidden-import agent.config ^
  --hidden-import agent.local_config ^
  --hidden-import agent.runtime_paths ^
  --hidden-import agent.service ^
  --hidden-import agent.sources ^
  --hidden-import agent.uploader ^
  --add-data "webui.html;." ^
  --add-data "ui.html;." ^
  run_bridge.py
if errorlevel 1 (
  echo Build failed.
  exit /b 1
)
echo.
echo Build finished:
echo %cd%\dist\teardown-room-bridge\
