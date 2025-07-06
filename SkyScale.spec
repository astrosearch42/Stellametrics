# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Main\\SkyScale.py'],
    pathex=[],
    binaries=[],
    datas=[('objects_png', 'objects_png'), ('Main/ImageViewer.ui', 'Main'), ('Library/distance_library.json', 'Library'), ('Library/de421.bsp', 'Library'), ('preset', 'preset')],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='SkyScale',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
