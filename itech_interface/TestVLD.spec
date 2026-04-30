# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['build_portable.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=['itech_interface', 'itech_interface.main', 'itech_interface.gui', 'itech_interface.controller', 'itech_interface.network', 'itech_interface.excel_handler'],
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
    name='TestVLD',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    name='TestVLD',
)
