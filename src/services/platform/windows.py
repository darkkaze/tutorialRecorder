"""
Windows platform service implementation.

This module provides Windows-specific implementation using FFmpeg's
dshow and gdigrab frameworks for device detection and recording.

Note: Implementation complete but not tested on Windows.
"""
import subprocess
import re
import tempfile
from pathlib import Path
from typing import Dict
from .base import BasePlatformService


class WindowsPlatformService(BasePlatformService):
    """Windows platform service using dshow and gdigrab frameworks."""

    def list_audio_devices(self) -> list[str]:
        """
        List all available audio input devices using DirectShow.

        Returns:
            List of audio device strings formatted as "name".

        Raises:
            RuntimeError: If FFmpeg is not available or fails to execute.
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-f", "dshow", "-list_devices", "true", "-i", "dummy"],
                capture_output=True,
                text=True,
                timeout=5
            )
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg and add it to PATH.")
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg command timed out.")

        return self._parse_audio_devices(result.stderr)

    def list_video_devices(self) -> list[str]:
        """
        List all available video input devices (webcams) using DirectShow.

        Returns:
            List of video device strings formatted as "name".

        Raises:
            RuntimeError: If FFmpeg is not available or fails to execute.
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-f", "dshow", "-list_devices", "true", "-i", "dummy"],
                capture_output=True,
                text=True,
                timeout=5
            )
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg and add it to PATH.")
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg command timed out.")

        return self._parse_video_devices(result.stderr)

    def get_screen_capture_device(self) -> str:
        """
        Get the screen capture device identifier for Windows.

        Returns:
            Screen capture device string (always "desktop" for gdigrab).
        """
        return "desktop"

    def build_audio_recording_command(
        self,
        device_name: str,
        project_name: str,
        index: int,
        temp_folder: Path
    ) -> list[str]:
        """
        Build FFmpeg command for audio recording using DirectShow.

        Args:
            device_name: DirectShow audio device name.
            project_name: Name of the project.
            index: Microphone index (1-based).
            temp_folder: Path to temporary folder.

        Returns:
            FFmpeg command as list of strings.
        """
        output_file = temp_folder / f"{project_name}_mic{index}.wav"

        cmd = [
            "ffmpeg",
            "-f", "dshow",
            "-i", f"audio={device_name}",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            str(output_file)
        ]

        return cmd

    def build_video_recording_command(
        self,
        device_name: str,
        project_name: str,
        temp_folder: Path
    ) -> list[str]:
        """
        Build FFmpeg command for video recording using DirectShow.

        Args:
            device_name: DirectShow video device name.
            project_name: Name of the project.
            temp_folder: Path to temporary folder.

        Returns:
            FFmpeg command as list of strings.
        """
        output_file = temp_folder / f"{project_name}_webcam.mp4"

        cmd = [
            "ffmpeg",
            "-f", "dshow",
            "-video_size", "1920x1080",
            "-framerate", "30",
            "-i", f"video={device_name}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            str(output_file)
        ]

        return cmd

    def build_screen_recording_command(
        self,
        device_name: str,
        screen_area: Dict,
        project_name: str,
        temp_folder: Path
    ) -> list[str]:
        """
        Build FFmpeg command for screen recording using gdigrab.

        Args:
            device_name: Screen device (always "desktop").
            screen_area: Dictionary with x, y, width, height.
            project_name: Name of the project.
            temp_folder: Path to temporary folder.

        Returns:
            FFmpeg command as list of strings.
        """
        output_file = temp_folder / f"{project_name}_screen.mp4"

        x = screen_area['x']
        y = screen_area['y']
        width = screen_area['width']
        height = screen_area['height']

        cmd = [
            "ffmpeg",
            "-f", "gdigrab",
            "-framerate", "30",
            "-offset_x", str(x),
            "-offset_y", str(y),
            "-video_size", f"{width}x{height}",
            "-i", device_name,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            str(output_file)
        ]

        return cmd

    def get_temp_directory(self, project_name: str, timestamp: str) -> Path:
        """
        Get temporary directory for recording files.

        Args:
            project_name: Name of the project.
            timestamp: ISO format timestamp.

        Returns:
            Path to created temporary directory.
        """
        # Sanitize project name for Windows (remove invalid characters)
        invalid_chars = '<>:"/\\|?*'
        sanitized_name = project_name
        for char in invalid_chars:
            sanitized_name = sanitized_name.replace(char, '_')

        # Use system temp directory
        temp_base = Path(tempfile.gettempdir())
        temp_folder = temp_base / "tutorialRecorder" / sanitized_name
        temp_folder.mkdir(parents=True, exist_ok=True)

        return temp_folder

    def _parse_audio_devices(self, output: str) -> list[str]:
        """
        Parse DirectShow output to extract audio devices.

        DirectShow output format:
        [dshow @ ...] "Device Name" (audio)

        Args:
            output: Output from FFmpeg dshow list_devices command.

        Returns:
            List of device name strings.
        """
        devices = []
        lines = output.split('\n')

        in_audio_section = False
        for line in lines:
            # Detect audio devices section
            if 'DirectShow audio devices' in line:
                in_audio_section = True
                continue
            elif 'DirectShow video devices' in line:
                in_audio_section = False
                continue

            if in_audio_section:
                # Match pattern: [dshow @ ...] "Device Name"
                match = re.search(r'\[dshow.*?\]\s+"([^"]+)"', line)
                if match:
                    device_name = match.group(1)
                    devices.append(device_name)

        if not devices:
            raise RuntimeError("No audio devices found. Check DirectShow device permissions.")

        return devices

    def _parse_video_devices(self, output: str) -> list[str]:
        """
        Parse DirectShow output to extract video devices.

        DirectShow output format:
        [dshow @ ...] "Device Name" (video)

        Args:
            output: Output from FFmpeg dshow list_devices command.

        Returns:
            List of device name strings.
        """
        devices = []
        lines = output.split('\n')

        in_video_section = False
        for line in lines:
            # Detect video devices section
            if 'DirectShow video devices' in line:
                in_video_section = True
                continue
            elif 'DirectShow audio devices' in line:
                in_video_section = False
                continue

            if in_video_section:
                # Match pattern: [dshow @ ...] "Device Name"
                match = re.search(r'\[dshow.*?\]\s+"([^"]+)"', line)
                if match:
                    device_name = match.group(1)
                    # Skip "Alternative name" entries
                    if not line.strip().startswith('@'):
                        devices.append(device_name)

        if not devices:
            raise RuntimeError("No video devices found. Check DirectShow device permissions.")

        return devices
