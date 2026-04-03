# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('extract_metadata.py', '.'), ('fill_form.py', '.'), ('tag_lookup.py', '.')],
    hiddenimports=['mutagen', 'mutagen.mp3', 'mutagen.id3', 'mutagen.flac', 'mutagen.wave', 'mutagen.oggvorbis', 'mutagen.aiff', 'mutagen.asf', 'mutagen.mp4', 'openpyxl', 'tkinterdnd2', 'tkcalendar', 'babel.numbers', 'ttkbootstrap'],
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
    name='RAO_Report',
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
