# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_bridge.py'],
    pathex=[],
    binaries=[],
    datas=[('webui.html', '.'), ('ui.html', '.')],
    hiddenimports=['app', 'agent.config', 'agent.local_config', 'agent.runtime_paths', 'agent.service', 'agent.sources', 'agent.uploader'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='teardown-room-bridge-v14',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='teardown-room-bridge-v14',
)
