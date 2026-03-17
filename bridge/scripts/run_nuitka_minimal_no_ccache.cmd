@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64
if errorlevel 1 exit /b 1
cd /d D:\serverhud\bridge
C:\Users\18621\AppData\Local\Programs\Python\Python313\python.exe -m nuitka --mode=standalone --disable-ccache --remove-output run_bridge.py
