$env:TEARDOWN_SAVEGAME_XML="$env:LOCALAPPDATA\Teardown\savegame.xml"
$env:POLL_INTERVAL="0.2"
$env:UPLOAD_INTERVAL="1.0"
python -m uvicorn app:app --host 127.0.0.1 --port 8787
Start-Process "http://127.0.0.1:8787/"
