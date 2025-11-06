# Troubleshooting

Common issues and solutions for TutorialRecorder.

## Permission Issues

### App keeps asking for screen recording/camera/microphone permissions every time

**Symptoms:**
- Permission dialog appears every time you launch the app
- Permissions are already granted in System Preferences
- App works fine after granting permissions, but forgets them on next launch

**Solution:**
This is usually caused by macOS TCC (Transparency, Consent, and Control) database getting into an inconsistent state.

**Steps to fix:**
1. Close TutorialRecorder completely
2. Open System Preferences → Security & Privacy → Privacy
3. Go to each permission type (Camera, Microphone, Screen Recording)
4. Find TutorialRecorder in the list and **remove it** (click the - button)
5. Close System Preferences
6. Launch TutorialRecorder again
7. Grant permissions when prompted
8. Permissions should now persist correctly

**Note:** This issue is more common with unsigned/ad-hoc signed apps. If the problem persists, you may need to sign the app with a Developer ID certificate.

---

### "TutorialRecorder.app is damaged and can't be opened" on first launch

**Symptoms:**
- macOS shows a dialog saying the app is damaged
- This happens when downloading from GitHub Releases

**Solution:**
This is macOS Gatekeeper quarantine. Run this command in Terminal:

```bash
xattr -cr /path/to/TutorialRecorder.app
```

Or, if you downloaded the DMG:
```bash
xattr -cr ~/Downloads/TutorialRecorder-1.0.0.dmg
```

Then open the app normally.

---

### Permission dialog doesn't appear / App doesn't ask for permissions

**Symptoms:**
- App launches but can't access camera/microphone/screen
- No permission dialog appears

**Solution:**
macOS may have blocked the permission request. Manually grant permissions:

1. Open System Preferences → Security & Privacy → Privacy
2. For each permission type:
   - Click the lock icon (bottom left) to unlock
   - Select Camera/Microphone/Screen Recording from left sidebar
   - Click the + button
   - Navigate to TutorialRecorder.app and add it
   - Check the checkbox next to TutorialRecorder
3. Restart TutorialRecorder

---

## Recording Issues

### FFmpeg error: "No such file or directory: 'ffmpeg'"

**Symptoms:**
- Recording starts but fails immediately
- Error message mentions FFmpeg not found

**Solution:**

**For pre-built app (from Releases):**
- FFmpeg should be bundled. Try re-downloading the app from GitHub Releases.

**For running from source:**
- Install FFmpeg: `brew install ffmpeg`
- Verify installation: `which ffmpeg`

---

### No audio devices detected

**Symptoms:**
- "No audio devices found" message
- Dropdown shows no microphones

**Solution:**
1. Check System Preferences → Security & Privacy → Privacy → Microphone
2. Ensure TutorialRecorder has permission
3. Restart the app
4. If still not working, run from terminal to see errors:
   ```bash
   /Applications/TutorialRecorder.app/Contents/MacOS/TutorialRecorder
   ```

---

### No video devices detected / Webcam not showing

**Symptoms:**
- "No video devices found" message
- Camera dropdown is empty

**Solution:**
1. Close any other apps using the camera (Zoom, FaceTime, etc.)
2. Check System Preferences → Security & Privacy → Privacy → Camera
3. Ensure TutorialRecorder has permission
4. Restart the app

---

### Screen recording produces black video

**Symptoms:**
- Recording completes successfully
- Video file exists but shows only black screen

**Solution:**
1. Check Screen Recording permission:
   - System Preferences → Security & Privacy → Privacy → Screen Recording
   - TutorialRecorder should be checked
2. **Important:** You MUST restart the app after granting Screen Recording permission
3. Try recording again

**Note:** Screen Recording permission requires app restart to take effect.

---

### Export fails / Can't create merged video

**Symptoms:**
- Recording works fine
- Export button fails or shows error

**Solution:**
1. Check that all recording files exist in project folder:
   - screen.mp4
   - webcam.mp4
   - mic1.wav (or mic2.wav, etc.)
2. Ensure you have write permissions in the export folder
3. Check available disk space (exports can be large)
4. Try exporting to a different folder

---

## Build Issues (for developers)

### PyInstaller fails with module not found

**Symptoms:**
- Build fails with "No module named 'X'"

**Solution:**
1. Activate virtual environment: `source venv/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Clean build: `rm -rf .build dist/macos`
4. Rebuild: `./build_macos.sh`

---

### DMG creation fails

**Symptoms:**
- App builds successfully but DMG creation fails
- Error: "create-dmg: command not found"

**Solution:**
Install create-dmg:
```bash
brew install create-dmg
```

Then rebuild.

---

## macOS Version Specific Issues

### macOS Sequoia (15.x) - Weekly/Monthly permission prompts

**Symptoms:**
- App asks for screen recording permission weekly or monthly
- This is a macOS Sequoia feature, not a bug in TutorialRecorder

**Workaround:**
- Unfortunately, this is Apple's new security model in Sequoia
- Only apps signed with Developer ID can avoid these prompts
- For personal use, you can use tools like "Amnesia" to extend permission durations

---

### macOS Ventura/Sonoma - "Allow for 1 month" button

**Symptoms:**
- Permission dialog shows "Allow for 1 month" option
- Permission expires after a month

**Solution:**
- This is expected macOS behavior for unsigned apps
- Select "Allow" and permissions should last longer
- For permanent solution, the app needs Developer ID signing

---

## Still Having Issues?

If none of these solutions work:

1. **Check logs:** Run the app from Terminal to see detailed errors
2. **Report issue:** [Create a GitHub issue](https://github.com/darkkaze/tutorialRecorder/issues) with:
   - macOS version
   - Error messages or screenshots
   - Steps to reproduce
   - Console output if available

3. **Try running from source:**
   ```bash
   git clone <repository-url>
   cd tutorialRecorder
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python src/main.py
   ```

---

## Getting Help

- **GitHub Issues:** [Report bugs](https://github.com/darkkaze/tutorialRecorder/issues)
- **Discussions:** Ask questions in GitHub Discussions
- **README:** Check the [main README](README.md) for setup instructions
