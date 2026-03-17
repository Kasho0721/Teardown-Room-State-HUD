@echo off
cd /d %~dp0
if exist dist\teardown-room-bridge\teardown-room-bridge.exe (
  start "" dist\teardown-room-bridge\teardown-room-bridge.exe
  exit /b 0
)
python -m uvicorn app:app --host 127.0.0.1 --port 8787
start "" http://127.0.0.1:8787/
