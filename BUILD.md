# Building TutorialRecorder

Instructions for building distributable packages for each platform.

## Pre-built Binaries

Pre-built binaries are available in the `dist/` folder:
- `dist/macos/` - macOS builds (.app and .dmg)
- `dist/windows/` - Windows builds (coming soon)
- `dist/linux/` - Linux builds (coming soon)

If you just want to use the app, download from `dist/` and skip the build process.

## macOS

### Prerequisites

```bash
# Install PyInstaller
pip install pyinstaller

# Optional: Install create-dmg for .dmg creation
brew install create-dmg
```

### Build

```bash
# Make script executable (first time only)
chmod +x build_macos.sh

# Run build
./build_macos.sh
```

### Output

Files will be created in `dist/macos/`:
- `TutorialRecorder.app` - Drag to Applications folder
- `TutorialRecorder-1.0.0.dmg` - Distributable installer

Temporary build files are in `.build/` (can be safely deleted).

### Manual Build

If you prefer to build manually:

```bash
# Build .app
pyinstaller --distpath .build/dist --workpath .build/work TutorialRecorder.spec

# Move to final location
mkdir -p dist/macos
mv .build/dist/TutorialRecorder.app dist/macos/

# Create DMG (optional)
create-dmg \
  --volname "TutorialRecorder" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "TutorialRecorder.app" 200 190 \
  --app-drop-link 600 185 \
  "dist/macos/TutorialRecorder-1.0.0.dmg" \
  "dist/macos/TutorialRecorder.app"
```

## Windows

**Status:** Not yet implemented

Build script will be located at `build_windows.bat`

Output will be in `dist/windows/`:
- `TutorialRecorder.exe`
- Installer (NSIS or similar)

## Linux

**Status:** Not yet implemented

Build script will be located at `build_linux.sh`

Output will be in `dist/linux/`:
- `TutorialRecorder.AppImage` or `.deb` package

## Troubleshooting

### PyInstaller not found
```bash
pip install pyinstaller
```

### create-dmg not found (macOS)
```bash
brew install create-dmg
```

### Missing dependencies
Make sure you're in a virtual environment with all dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
```

### Build fails
1. Clean previous builds: `rm -rf .build dist`
2. Try again: `./build_macos.sh`
3. Check that FFmpeg is installed: `ffmpeg -version`

## Distribution

### macOS
- Distribute the `.dmg` file
- Users can drag the app to Applications
- First run requires: System Preferences → Security & Privacy → Allow

### Windows
- Distribute the installer or `.exe`
- Users may need to allow in Windows Defender

### Linux
- Distribute `.AppImage` (no installation) or `.deb` (Debian/Ubuntu)

## Code Signing (Optional)

For production releases, you should code sign the applications:

### macOS
```bash
# Sign the .app
codesign --deep --force --verify --verbose --sign "Developer ID" dist/macos/TutorialRecorder.app

# Notarize with Apple
xcrun notarytool submit dist/macos/TutorialRecorder-1.0.0.dmg --wait
```

### Windows
Use `signtool.exe` with a code signing certificate.
