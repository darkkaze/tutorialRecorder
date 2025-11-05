"""
Recording service.

This module provides functionality to record audio and video inputs
using FFmpeg, with synchronized timestamps across all sources.

Available classes:
- RecordingSession: Manages active recording session with multiple inputs.

Available functions:
- start_recording(config): Start a new recording session.
- export_project(temp_folder, dest_folder, project_name): Export recorded files.

Note: Requires FFmpeg to be installed and available in PATH.
"""
import subprocess
import signal
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict
import json
import shutil
from models.project import ProjectConfig


class RecordingSession:
    """
    Manages an active recording session with multiple inputs.

    Tracks all FFmpeg subprocesses and provides methods to control
    the recording (pause, resume, stop).
    """

    def __init__(self, project_name: str, start_timestamp: str, temp_folder: Path):
        """
        Initialize recording session.

        Args:
            project_name: Name of the project.
            start_timestamp: ISO format timestamp when recording started.
            temp_folder: Path to temporary folder for recordings.
        """
        self.project_name = project_name
        self.start_timestamp = start_timestamp
        self.temp_folder = temp_folder
        self.processes: Dict[str, subprocess.Popen] = {}
        self.pause_timestamps = []
        self.is_paused = False

    def add_process(self, name: str, process: subprocess.Popen):
        """
        Add a subprocess to the recording session.

        Args:
            name: Identifier for the process (e.g., "mic1", "webcam").
            process: The FFmpeg subprocess.
        """
        self.processes[name] = process

    def pause_recording(self):
        """Pause all recording processes using SIGSTOP."""
        if self.is_paused:
            return

        for process in self.processes.values():
            process.send_signal(signal.SIGSTOP)

        self.pause_timestamps.append({
            "action": "pause",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self.is_paused = True

    def resume_recording(self):
        """Resume all recording processes using SIGCONT."""
        if not self.is_paused:
            return

        for process in self.processes.values():
            process.send_signal(signal.SIGCONT)

        self.pause_timestamps.append({
            "action": "resume",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self.is_paused = False

    def stop_recording(self) -> str:
        """
        Stop all recording processes and save metadata.

        Returns:
            Path to the temporary folder containing recordings.
        """
        for process in self.processes.values():
            try:
                if process.stdin:
                    process.stdin.write(b'q')
                    process.stdin.flush()
            except Exception:
                try:
                    process.terminate()
                except Exception:
                    pass

        for name, process in self.processes.items():
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                    process.wait(timeout=2)
                except Exception:
                    pass

        self._save_metadata()
        return str(self.temp_folder)

    def _save_metadata(self):
        """Save recording metadata to JSON file."""
        metadata = {
            "project_name": self.project_name,
            "start_timestamp": self.start_timestamp,
            "stop_timestamp": datetime.now(timezone.utc).isoformat(),
            "pause_events": self.pause_timestamps,
            "recordings": list(self.processes.keys())
        }

        metadata_path = self.temp_folder / f"{self.project_name}_metadata.json"
        with metadata_path.open('w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)


def start_recording(config: ProjectConfig) -> RecordingSession:
    """
    Start a new recording session with all configured inputs.

    Args:
        config: Project configuration with input devices.

    Returns:
        Active RecordingSession instance.

    Raises:
        RuntimeError: If FFmpeg is not available or fails to start.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    temp_folder = _create_temp_folder(config["name"], timestamp)
    session = RecordingSession(config["name"], timestamp, temp_folder)

    for idx, audio_input in enumerate(config["audio_inputs"], start=1):
        process = _start_audio_recording(
            audio_input["device_name"],
            config["name"],
            idx,
            temp_folder
        )
        session.add_process(f"mic{idx}", process)

    for idx, video_input in enumerate(config["video_inputs"], start=1):
        if video_input["source_type"] == "screen":
            if config["screen_area"]:
                process = _start_screen_recording(
                    video_input["device_name"],
                    config["screen_area"],
                    config["name"],
                    temp_folder
                )
                session.add_process("screen", process)
        else:
            process = _start_video_recording(
                video_input["device_name"],
                config["name"],
                temp_folder
            )
            session.add_process("webcam", process)

    return session


def _start_audio_recording(
    device_name: str,
    project_name: str,
    index: int,
    temp_folder: Path
) -> subprocess.Popen:
    """
    Start audio recording using FFmpeg.

    Args:
        device_name: Name of the audio device (platform-specific format).
        project_name: Name of the project.
        index: Index of the microphone (1-based).
        temp_folder: Path to temporary folder.

    Returns:
        FFmpeg subprocess.

    Raises:
        RuntimeError: If FFmpeg fails to start.
    """
    from .platform import get_platform_service
    platform_service = get_platform_service()
    cmd = platform_service.build_audio_recording_command(
        device_name, project_name, index, temp_folder
    )

    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Please install FFmpeg.")


def _start_video_recording(
    device_name: str,
    project_name: str,
    temp_folder: Path
) -> subprocess.Popen:
    """
    Start video recording using FFmpeg.

    Args:
        device_name: Name of the video device (platform-specific format).
        project_name: Name of the project.
        temp_folder: Path to temporary folder.

    Returns:
        FFmpeg subprocess.

    Raises:
        RuntimeError: If FFmpeg fails to start.
    """
    from .platform import get_platform_service
    platform_service = get_platform_service()
    cmd = platform_service.build_video_recording_command(
        device_name, project_name, temp_folder
    )

    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Please install FFmpeg.")


def _start_screen_recording(
    device_name: str,
    screen_area: Dict,
    project_name: str,
    temp_folder: Path
) -> subprocess.Popen:
    """
    Start screen recording using FFmpeg with crop filter.

    Args:
        device_name: Name of the screen capture device (platform-specific format).
        screen_area: Dictionary with x, y, width, height.
        project_name: Name of the project.
        temp_folder: Path to temporary folder.

    Returns:
        FFmpeg subprocess.

    Raises:
        RuntimeError: If FFmpeg fails to start.
    """
    from .platform import get_platform_service
    platform_service = get_platform_service()
    cmd = platform_service.build_screen_recording_command(
        device_name, screen_area, project_name, temp_folder
    )

    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Please install FFmpeg.")


def _create_temp_folder(project_name: str, timestamp: str) -> Path:
    """
    Create temporary folder for recording files.

    Args:
        project_name: Name of the project.
        timestamp: ISO format timestamp.

    Returns:
        Path to created temporary folder.
    """
    from .platform import get_platform_service
    platform_service = get_platform_service()
    return platform_service.get_temp_directory(project_name, timestamp)


def export_project(temp_folder: str, dest_folder: str, project_name: str):
    """
    Export recorded files from temp folder to destination.

    Args:
        temp_folder: Path to temporary folder with recordings.
        dest_folder: Destination folder for export.
        project_name: Name of the project.

    Raises:
        FileNotFoundError: If temp folder does not exist.
        IOError: If file copy fails.
    """
    temp_path = Path(temp_folder)
    dest_path = Path(dest_folder) / project_name

    if not temp_path.exists():
        raise FileNotFoundError(f"Temp folder not found: {temp_folder}")

    dest_path.mkdir(parents=True, exist_ok=True)

    for file in temp_path.glob("*"):
        file_name = file.name.replace(f"{project_name}_", "")
        dest_file = dest_path / file_name
        shutil.copy2(file, dest_file)
