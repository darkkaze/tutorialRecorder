# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[
        ('/opt/homebrew/bin/ffmpeg', '.'),
        ('/opt/homebrew/Cellar/ffmpeg/8.0_1/lib/libavdevice.62.dylib', 'lib'),
        ('/opt/homebrew/Cellar/ffmpeg/8.0_1/lib/libavfilter.11.dylib', 'lib'),
        ('/opt/homebrew/Cellar/ffmpeg/8.0_1/lib/libavformat.62.dylib', 'lib'),
        ('/opt/homebrew/Cellar/ffmpeg/8.0_1/lib/libavcodec.62.dylib', 'lib'),
        ('/opt/homebrew/Cellar/ffmpeg/8.0_1/lib/libswresample.6.dylib', 'lib'),
        ('/opt/homebrew/Cellar/ffmpeg/8.0_1/lib/libswscale.9.dylib', 'lib'),
        ('/opt/homebrew/Cellar/ffmpeg/8.0_1/lib/libavutil.60.dylib', 'lib'),
    ],
    datas=[],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtSvg',
        'qt_material',
        'windows.start_screen',
        'windows.project_config_window',
        'windows.project_viewer_window',
        'windows.recording_toolbar',
        'widgets.screen_selector',
        'services.audio_service',
        'services.video_service',
        'services.recording_service',
        'services.config_service',
        'services.project_service',
        'services.export_service',
        'services.platform.base',
        'services.platform.macos',
        'services.platform.windows',
        'services.platform.linux',
        'models.project',
        'utils.ffmpeg_utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TutorialRecorder',
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TutorialRecorder',
)

app = BUNDLE(
    coll,
    name='TutorialRecorder.app',
    icon='icon.icns',
    bundle_identifier='dev.nomada.tutorialrecorder',
    version='1.0.1',
    info_plist={
        'CFBundleName': 'TutorialRecorder',
        'CFBundleDisplayName': 'TutorialRecorder',
        'CFBundleShortVersionString': '1.0.1',
        'CFBundleVersion': '1.0.1',
        'NSHumanReadableCopyright': 'Copyright © 2025 Kaze. Licensed under Beerware License.',
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.13.0',
        'NSCameraUsageDescription': 'TutorialRecorder needs access to your camera to record webcam video.',
        'NSMicrophoneUsageDescription': 'TutorialRecorder needs access to your microphone to record audio.',
        'NSScreenCaptureDescription': 'TutorialRecorder needs access to screen recording to capture your screen.',
    },
    entitlements_file='entitlements.plist',
)
