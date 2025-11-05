# TutorialRecorder - Project Guide for Claude

## IMPORTANT
**Always follow the global CLAUDE.md configuration** (`~/.claude/CLAUDE.md`). The settings there (coding principles, style guide, git configuration, etc.) take precedence over this document.

---

## Project Overview

Multi-channel screen and audio recording tool for creating tutorials. Records multiple audio inputs, webcam, and screen capture simultaneously with perfect synchronization. Each source is saved as a separate file with timestamps for easy post-production editing.

**Current Status:** macOS fully implemented (2025/11/04)

---

## Technology Stack

- **UI Framework:** PyQt6 with custom widgets
- **Recording:** FFmpeg via subprocess (avfoundation on macOS)
- **Architecture:** Platform abstraction layer for multi-OS support
- **Configuration:** JSON files in user home directory

---

## Code Organization

### Structure
```
src/
├── main.py                      # Entry point
├── models/                      # Data models (TypedDict)
│   └── project.py              # ProjectConfig, AudioInput, VideoInput, etc.
├── services/                    # Business logic
│   ├── platform/               # Platform-specific implementations
│   │   ├── base.py            # Abstract interface (8 methods)
│   │   ├── macos.py           # macOS implementation (avfoundation)
│   │   ├── windows.py         # Stub (NotImplementedError)
│   │   └── linux.py           # Stub (NotImplementedError)
│   ├── audio_service.py       # Audio device detection
│   ├── video_service.py       # Video device detection
│   ├── recording_service.py   # Recording control & FFmpeg management
│   ├── config_service.py      # User preferences (~/.tutorialRecording/config.json)
│   └── project_service.py     # Project management
├── widgets/                     # Reusable UI components
│   └── screen_selector.py     # Transparent overlay for area selection
└── windows/                     # Main application windows
    ├── project_config_window.py # Main configuration window
    └── recording_toolbar.py     # Toolbar during recording
```

### Key Design Patterns

**Platform Abstraction:**
- All platform-specific code is isolated in `services/platform/`
- Services use dependency injection via factory pattern (`get_platform_service()`)
- To add Windows/Linux support: implement the 8 abstract methods in respective platform files

**Service Layer:**
- Thin service interfaces delegate to platform implementations
- Recording service manages FFmpeg subprocesses with pause/resume/stop control
- Config service persists user preferences (export path, default resolution)

**UI Components:**
- Main window (`project_config_window.py`) handles project configuration
- Screen selector (`screen_selector.py`) provides visual area selection with drag-to-move
- All widgets follow PyQt6 best practices with signals/slots

---

## Recording Flow

1. User configures project (name, audio inputs, video source, export path)
2. Click "Seleccionar Área" → shows transparent overlay
3. User drags/resizes selection rectangle, chooses resolution
4. Click "Grabar" → starts all FFmpeg processes simultaneously
5. System tray icon allows stopping recording
6. Stop → sends 'q' to FFmpeg stdin for graceful shutdown
7. Files exported to user-selected folder with metadata JSON

---

## FFmpeg Integration

**Commands are built by platform service:**
- Audio: WAV format, direct device capture
- Webcam: MP4, H.264, preset=medium, CRF=20
- Screen: MP4, H.264, crop filter for selected area

**Process Management:**
- All processes started with stdin/stdout/stderr pipes
- Graceful shutdown via 'q' command to FFmpeg stdin
- Fallback to SIGTERM/SIGKILL with timeouts
- Metadata JSON tracks timestamps and pause events

---

## Configuration Storage

**User config:** `~/.tutorialRecording/config.json`
```json
{
  "export_path": "/path/to/exports",
  "default_resolution": "1920x1080"
}
```

**Recording metadata:** `{temp_folder}/{project_name}_metadata.json`
```json
{
  "project_name": "...",
  "start_timestamp": "...",
  "stop_timestamp": "...",
  "pause_events": [...],
  "recordings": ["mic1", "mic2", "webcam", "screen"]
}
```

---

## Adding New Platform Support

1. Open `src/services/platform/{windows|linux}.py`
2. Implement the 8 abstract methods from `base.py`:
   - `list_audio_devices()`
   - `list_video_devices()`
   - `get_screen_capture_device()`
   - `build_audio_recording_command()`
   - `build_video_recording_command()`
   - `build_screen_recording_command()`
   - `get_temp_directory()`
3. Use appropriate FFmpeg input format (dshow for Windows, v4l2/alsa for Linux)
4. Test device detection and recording
5. No changes needed in other files (abstraction handles it)

---

## Development Notes

- Always use virtual environment: `source venv/bin/activate`
- FFmpeg must be installed and in PATH
- Device strings format is platform-specific (macOS uses "index:name")
- Screen coordinates are global screen coordinates, not window-relative
- All timestamps use ISO format with UTC timezone
- Git commits follow conventional commits style with Claude Code footer

---

## Testing

Currently manual testing only. To test:
1. Run `python src/main.py`
2. Configure project with available devices
3. Select screen area and start recording
4. Verify all files are created in export folder
5. Check synchronization by comparing timestamps in metadata JSON

---

## Known Limitations

- macOS only (Windows/Linux stubs exist but not implemented)
- No built-in editor (files must be edited externally)
- No output template merging (manual merge in video editor required)
- Not packaged as executable (runs from source)

---

**Remember:** Always refer to `~/.claude/CLAUDE.md` for coding standards, commit message format, and project-wide conventions.
