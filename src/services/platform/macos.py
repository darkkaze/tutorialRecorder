"""
macOS platform service implementation.

This module provides macOS-specific implementation using FFmpeg's
avfoundation framework for device detection and recording.
"""
import subprocess
import re
import tempfile
from pathlib import Path
from typing import Dict
from .base import BasePlatformService
from utils.ffmpeg_utils import get_ffmpeg_path


class MacOSPlatformService(BasePlatformService):
    """macOS platform service using avfoundation framework."""

    def list_audio_devices(self) -> list[str]:
        """
        List all available audio input devices.

        Returns:
            List of audio device strings formatted as "index:name".

        Raises:
            RuntimeError: If FFmpeg is not available or fails to execute.
        """
        try:
            result = subprocess.run(
                [get_ffmpeg_path(), "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                capture_output=True,
                text=True,
                timeout=5
            )
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg command timed out.")

        return self._parse_audio_devices(result.stderr)

    def list_video_devices(self) -> list[str]:
        """
        List all available video input devices (webcams).

        Returns:
            List of video device strings formatted as "index:name".

        Raises:
            RuntimeError: If FFmpeg is not available or fails to execute.
        """
        try:
            result = subprocess.run(
                [get_ffmpeg_path(), "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                capture_output=True,
                text=True,
                timeout=5
            )
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg command timed out.")

        return self._parse_video_devices(result.stderr)

    def get_screen_capture_device(self) -> str:
        """
        Get the screen capture device identifier for macOS.

        Returns:
            Screen capture device string formatted as "index:name".

        Raises:
            RuntimeError: If FFmpeg is not available or screen capture not found.
        """
        try:
            result = subprocess.run(
                [get_ffmpeg_path(), "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                capture_output=True,
                text=True,
                timeout=5
            )
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg command timed out.")

        screen_device = self._parse_screen_capture(result.stderr)
        if not screen_device:
            raise RuntimeError("Screen capture device not found.")

        return screen_device

    def build_audio_recording_command(
        self,
        device_name: str,
        project_name: str,
        index: int,
        temp_folder: Path
    ) -> list[str]:
        """
        Build FFmpeg command for audio recording using avfoundation.

        Args:
            device_name: Audio device identifier (format: "index:name").
            project_name: Name of the project.
            index: Index of the microphone (1-based).
            temp_folder: Path to temporary folder.

        Returns:
            FFmpeg command as list of strings.
        """
        device_index = device_name.split(":")[0] if ":" in device_name else device_name
        output_file = temp_folder / f"{project_name}_mic{index}.wav"

        return [
            get_ffmpeg_path(),
            "-f", "avfoundation",
            "-i", f":{device_index}",
            str(output_file)
        ]

    def build_video_recording_command(
        self,
        device_name: str,
        project_name: str,
        temp_folder: Path
    ) -> list[str]:
        """
        Build FFmpeg command for video recording using avfoundation.

        Args:
            device_name: Video device identifier (format: "index:name").
            project_name: Name of the project.
            temp_folder: Path to temporary folder.

        Returns:
            FFmpeg command as list of strings.
        """
        device_index = device_name.split(":")[0] if ":" in device_name else device_name
        output_file = temp_folder / f"{project_name}_webcam.mp4"

        return [
            get_ffmpeg_path(),
            "-f", "avfoundation",
            "-framerate", "30",
            "-i", f"{device_index}:none",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-bf", "2",
            "-maxrate", "5M",
            "-bufsize", "10M",
            "-movflags", "+faststart",
            str(output_file)
        ]

    def build_screen_recording_command(
        self,
        device_name: str,
        screen_area: Dict,
        project_name: str,
        temp_folder: Path
    ) -> list[str]:
        """
        Build FFmpeg command for screen recording with crop using avfoundation.

        Args:
            device_name: Screen capture device identifier (format: "index:name").
            screen_area: Dictionary with x, y, width, height.
            project_name: Name of the project.
            temp_folder: Path to temporary folder.

        Returns:
            FFmpeg command as list of strings.
        """
        device_index = device_name.split(":")[0] if ":" in device_name else device_name
        output_file = temp_folder / f"{project_name}_screen.mp4"

        crop_filter = (
            f"crop={screen_area['width']}:{screen_area['height']}:"
            f"{screen_area['x']}:{screen_area['y']}"
        )

        return [
            get_ffmpeg_path(),
            "-f", "avfoundation",
            "-i", f"{device_index}:none",
            "-filter:v", crop_filter,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-bf", "2",
            "-maxrate", "5M",
            "-bufsize", "10M",
            "-movflags", "+faststart",
            str(output_file)
        ]

    def get_temp_directory(self, project_name: str, timestamp: str) -> Path:
        """
        Get temporary directory for recording files on macOS.

        Args:
            project_name: Name of the project.
            timestamp: ISO format timestamp.

        Returns:
            Path to temporary folder.
        """
        # Sanitize project name (macOS doesn't allow : and /)
        sanitized_name = project_name.replace(':', '_').replace('/', '_')
        safe_timestamp = timestamp.replace(":", "-").replace(".", "-")
        folder_name = f"tutorialrecorder_{sanitized_name}_{safe_timestamp}"
        temp_folder = Path(tempfile.gettempdir()) / folder_name
        temp_folder.mkdir(parents=True, exist_ok=True)
        return temp_folder

    def _parse_audio_devices(self, ffmpeg_output: str) -> list[str]:
        """
        Parse FFmpeg avfoundation output to extract audio device names with indices.

        Args:
            ffmpeg_output: stderr output from FFmpeg list_devices command.

        Returns:
            List of audio device strings formatted as "index:name".
        """
        devices = []
        lines = ffmpeg_output.split('\n')
        in_audio_section = False

        for line in lines:
            if "AVFoundation audio devices:" in line:
                in_audio_section = True
                continue

            if "AVFoundation video devices:" in line:
                in_audio_section = False
                continue

            if in_audio_section:
                match = re.search(r'\[(\d+)\] (.+)', line)
                if match:
                    index = match.group(1)
                    name = match.group(2).strip()
                    devices.append(f"{index}:{name}")

        return devices

    def _parse_video_devices(self, ffmpeg_output: str) -> list[str]:
        """
        Parse FFmpeg avfoundation output to extract video device names with indices.

        Args:
            ffmpeg_output: stderr output from FFmpeg list_devices command.

        Returns:
            List of video device strings formatted as "index:name".
        """
        devices = []
        lines = ffmpeg_output.split('\n')
        in_video_section = False

        for line in lines:
            if "AVFoundation video devices:" in line:
                in_video_section = True
                continue

            if "AVFoundation audio devices:" in line:
                in_video_section = False
                continue

            if in_video_section:
                match = re.search(r'\[(\d+)\] (.+)', line)
                if match:
                    index = match.group(1)
                    device_name = match.group(2).strip()
                    if "screen" not in device_name.lower():
                        devices.append(f"{index}:{device_name}")

        return devices

    def _parse_screen_capture(self, ffmpeg_output: str) -> str | None:
        """
        Parse FFmpeg avfoundation output to extract screen capture device identifier.

        Args:
            ffmpeg_output: stderr output from FFmpeg list_devices command.

        Returns:
            Screen capture device string formatted as "index:name" or None if not found.
        """
        lines = ffmpeg_output.split('\n')
        in_video_section = False

        for line in lines:
            if "AVFoundation video devices:" in line:
                in_video_section = True
                continue

            if "AVFoundation audio devices:" in line:
                in_video_section = False
                continue

            if in_video_section:
                match = re.search(r'\[(\d+)\] (.+)', line)
                if match:
                    index = match.group(1)
                    device_name = match.group(2).strip()
                    if "screen" in device_name.lower():
                        return f"{index}:{device_name}"

        return None
