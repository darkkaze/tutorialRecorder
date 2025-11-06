#!/bin/bash
# Build script for macOS

set -e  # Exit on error

echo "🔧 Building TutorialRecorder for macOS..."
echo ""

# Check if pyinstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf .build dist/macos

# Build the .app bundle (PyInstaller outputs to build/ and dist/)
echo "📦 Building .app bundle with PyInstaller..."
pyinstaller --distpath .build/dist --workpath .build/work TutorialRecorder.spec

# Check if .app was created
if [ ! -d ".build/dist/TutorialRecorder.app" ]; then
    echo "❌ Build failed: TutorialRecorder.app not found"
    exit 1
fi

# Create final dist directory structure
echo "📁 Organizing output files..."
mkdir -p dist/macos

# Move .app to final location
mv .build/dist/TutorialRecorder.app dist/macos/

echo "✅ .app bundle created successfully!"
echo ""

# Create DMG (requires create-dmg)
echo "💿 Creating DMG installer..."

# Check if create-dmg is installed
if ! command -v create-dmg &> /dev/null; then
    echo "⚠️  create-dmg not found. Install with: brew install create-dmg"
    echo "   Skipping DMG creation. You can run manually later."
    echo ""
    echo "✅ Build complete! Find your app at:"
    echo "   dist/macos/TutorialRecorder.app"
    exit 0
fi

# Create DMG
create-dmg \
  --volname "TutorialRecorder" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "TutorialRecorder.app" 200 190 \
  --hide-extension "TutorialRecorder.app" \
  --app-drop-link 600 185 \
  "dist/macos/TutorialRecorder-1.0.0.dmg" \
  "dist/macos/TutorialRecorder.app" \
  2>/dev/null || {
    echo "⚠️  DMG creation had warnings (this is normal)"
  }

echo ""
echo "✅ Build complete!"
echo ""
echo "📦 Your files are in dist/macos/:"
echo "   - App bundle: TutorialRecorder.app"
if [ -f "dist/macos/TutorialRecorder-1.0.0.dmg" ]; then
    echo "   - DMG installer: TutorialRecorder-1.0.0.dmg"
fi
echo ""
echo "💡 Tip: You can delete .build/ folder (temporary files)"
echo ""
echo "🎉 Ready to distribute!"
