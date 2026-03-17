@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64
if errorlevel 1 exit /b 1
cd /d D:\serverhud\bridge
C:\Users\18621\AppData\Local\Programs\Python\Python313\python.exe -m nuitka --standalone --assume-yes-for-downloads --output-dir=dist --remove-output --windows-console-mode=disable --include-package=agent --include-data-files=web\webui.html=webui.html --include-data-files=web\ui.html=ui.html --include-data-files=bridge_config.json=bridge_config.json --output-filename=teardown-room-bridge-nuitka.exe run_bridge.py
