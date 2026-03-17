@echo off
cd /d D:\serverhud\bridge
.venv312\Scripts\python.exe -m nuitka --mode=standalone --disable-ccache --assume-yes-for-downloads --zig --remove-output --include-package=agent --include-data-files=web\webui.html=webui.html --include-data-files=web\ui.html=ui.html --include-data-files=bridge_config.json=bridge_config.json run_bridge.py
