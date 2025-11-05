"""
Linux platform service implementation.

This module provides Linux-specific implementation using FFmpeg's
x11grab, v4l2, and alsa frameworks for device detection and recording.

Note: Currently supports X11 only. Wayland support coming soon UwU
"""
import subprocess
import re
import os
import tempfile
from pathlib import Path
from typing import Dict
from .base import BasePlatformService


class LinuxPlatformService(BasePlatformService):
    """Linux platform service using x11grab, v4l2, and alsa frameworks."""

    def __init__(self):
        """Initialize Linux platform service and check for Wayland."""
        super().__init__()
        self._check_wayland_warning()

    def _check_wayland_warning(self):
        """Check if running on Wayland and show warning."""
        is_wayland = os.environ.get('WAYLAND_DISPLAY') is not None

        if is_wayland:
            try:
                from PyQt6.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Wayland Detected UwU")
                msg.setText("El software aún no está listo para tan moderna tecnología UwU")
                msg.setInformativeText(
                    "Este software actualmente solo soporta X11.\n\n"
                    "Wayland tiene protecciones de seguridad que requieren "
                    "implementación adicional usando xdg-desktop-portal.\n\n"
                    "Por favor ejecuta tu sesión en X11 por ahora. ><"
                )
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
            except ImportError:
                print("⚠️  Wayland detectado UwU - Este software solo soporta X11 por ahora")

    def list_audio_devices(self) -> list[str]:
        """
        List all available audio input devices using ALSA.

        Returns:
            List of audio device strings formatted as "hw:X,Y:name".

        Raises:
            RuntimeError: If arecord is not available or fails to execute.
        """
        try:
            result = subprocess.run(
                ["arecord", "-L"],
                capture_output=True,
                text=True,
                timeout=5
            )
        except FileNotFoundError:
            raise RuntimeError("arecord not found. Please install alsa-utils.")
        except subprocess.TimeoutExpired:
            raise RuntimeError("arecord command timed out.")

        return self._parse_audio_devices(result.stdout)

    def list_video_devices(self) -> list[str]:
        """
        List all available video input devices (webcams) using V4L2.

        Returns:
            List of video device strings formatted as "/dev/videoX:name".

        Raises:
            RuntimeError: If v4l2-ctl is not available or fails to execute.
        """
        devices = []
        video_files = Path("/dev").glob("video*")

        for device_path in sorted(video_files):
            try:
                result = subprocess.run(
                    ["v4l2-ctl", "--device", str(device_path), "--info"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )

                # Extract device name from output
                name_match = re.search(r'Card type\s*:\s*(.+)', result.stdout)
                device_name = name_match.group(1).strip() if name_match else device_path.name

                devices.append(f"{device_path}:{device_name}")
            except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
                # If v4l2-ctl not available, just use device path
                devices.append(f"{device_path}:{device_path.name}")

        if not devices:
            raise RuntimeError("No video devices found. Check /dev/video* permissions.")

        return devices

    def get_screen_capture_device(self) -> str:
        """
        Get the screen capture device identifier for Linux X11.

        Returns:
            X11 display identifier (usually ":0").

        Raises:
            RuntimeError: If DISPLAY environment variable is not set.
        """
        display = os.environ.get('DISPLAY')

        if not display:
            raise RuntimeError("DISPLAY environment variable not set. Are you running X11?")

        return f"X11:{display}"

    def build_audio_recording_command(
        self,
        device_name: str,
        project_name: str,
        index: int,
        temp_folder: Path
    ) -> list[str]:
        """
        Build FFmpeg command for audio recording using ALSA.

        Args:
            device_name: ALSA device string (e.g., "hw:0,0:Device Name").
            project_name: Name of the project.
            index: Microphone index (1-based).
            temp_folder: Path to temporary folder.

        Returns:
            FFmpeg command as list of strings.
        """
        # Extract device identifier (before colon)
        device_id = device_name.split(':')[0] if ':' in device_name else device_name

        output_file = temp_folder / f"{project_name}_mic{index}.wav"

        cmd = [
            "ffmpeg",
            "-f", "alsa",
            "-i", device_id,
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
        Build FFmpeg command for video recording using V4L2.

        Args:
            device_name: V4L2 device string (e.g., "/dev/video0:Webcam").
            project_name: Name of the project.
            temp_folder: Path to temporary folder.

        Returns:
            FFmpeg command as list of strings.
        """
        # Extract device path (before colon)
        device_path = device_name.split(':')[0] if ':' in device_name else device_name

        output_file = temp_folder / f"{project_name}_webcam.mp4"

        cmd = [
            "ffmpeg",
            "-f", "v4l2",
            "-framerate", "30",
            "-video_size", "1920x1080",
            "-i", device_path,
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
        Build FFmpeg command for screen recording using x11grab.

        Args:
            device_name: X11 display string (e.g., "X11::0").
            screen_area: Dictionary with x, y, width, height.
            project_name: Name of the project.
            temp_folder: Path to temporary folder.

        Returns:
            FFmpeg command as list of strings.
        """
        # Extract display (after "X11:")
        display = device_name.split('X11:')[1] if 'X11:' in device_name else ':0'

        output_file = temp_folder / f"{project_name}_screen.mp4"

        x = screen_area['x']
        y = screen_area['y']
        width = screen_area['width']
        height = screen_area['height']

        cmd = [
            "ffmpeg",
            "-f", "x11grab",
            "-framerate", "30",
            "-video_size", f"{width}x{height}",
            "-i", f"{display}+{x},{y}",
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
        # Sanitize project name (remove invalid characters for filesystem)
        sanitized_name = project_name.replace('/', '_').replace('\0', '_')

        # Use system temp directory
        temp_base = Path(tempfile.gettempdir())
        temp_folder = temp_base / "tutorialRecorder" / sanitized_name
        temp_folder.mkdir(parents=True, exist_ok=True)

        return temp_folder

    def _parse_audio_devices(self, output: str) -> list[str]:
        """
        Parse arecord output to extract audio devices.

        Args:
            output: Output from arecord -L command.

        Returns:
            List of device strings.
        """
        devices = []
        lines = output.strip().split('\n')

        for i, line in enumerate(lines):
            # Look for hw:X,Y devices
            if line.startswith('hw:'):
                device_id = line.strip()

                # Try to get description from next line
                description = ""
                if i + 1 < len(lines) and lines[i + 1].startswith(' '):
                    description = lines[i + 1].strip()

                device_str = f"{device_id}:{description}" if description else device_id
                devices.append(device_str)

        if not devices:
            # Fallback: try default device
            devices.append("default:Default Audio Device")

        return devices
