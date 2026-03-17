@echo off
cd /d D:\serverhud\bridge
C:\Users\18621\AppData\Local\Programs\Python\Python313\python.exe -m nuitka --mode=standalone --disable-ccache --assume-yes-for-downloads --zig --remove-output run_bridge.py
