"""
Base platform service interface.

This module defines the abstract interface that all platform-specific
implementations must follow.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict


class BasePlatformService(ABC):
    """
    Abstract base class for platform-specific services.

    Each platform (macOS, Windows, Linux) must implement this interface
    to provide device detection and FFmpeg command building.
    """

    @abstractmethod
    def list_audio_devices(self) -> list[str]:
        """
        List all available audio input devices.

        Returns:
            List of audio device names/identifiers.

        Raises:
            RuntimeError: If unable to detect devices.
        """
        pass

    @abstractmethod
    def list_video_devices(self) -> list[str]:
        """
        List all available video input devices (webcams).

        Returns:
            List of video device names/identifiers.

        Raises:
            RuntimeError: If unable to detect devices.
        """
        pass

    @abstractmethod
    def get_screen_capture_device(self) -> str:
        """
        Get the screen capture device identifier.

        Returns:
            Screen capture device identifier.

        Raises:
            RuntimeError: If screen capture not available.
        """
        pass

    @abstractmethod
    def build_audio_recording_command(
        self,
        device_name: str,
        project_name: str,
        index: int,
        temp_folder: Path
    ) -> list[str]:
        """
        Build FFmpeg command for audio recording.

        Args:
            device_name: Audio device identifier.
            project_name: Name of the project.
            index: Index of the microphone (1-based).
            temp_folder: Path to temporary folder.

        Returns:
            FFmpeg command as list of strings.
        """
        pass

    @abstractmethod
    def build_video_recording_command(
        self,
        device_name: str,
        project_name: str,
        temp_folder: Path
    ) -> list[str]:
        """
        Build FFmpeg command for video recording (webcam).

        Args:
            device_name: Video device identifier.
            project_name: Name of the project.
            temp_folder: Path to temporary folder.

        Returns:
            FFmpeg command as list of strings.
        """
        pass

    @abstractmethod
    def build_screen_recording_command(
        self,
        device_name: str,
        screen_area: Dict,
        project_name: str,
        temp_folder: Path
    ) -> list[str]:
        """
        Build FFmpeg command for screen recording with crop.

        Args:
            device_name: Screen capture device identifier.
            screen_area: Dictionary with x, y, width, height.
            project_name: Name of the project.
            temp_folder: Path to temporary folder.

        Returns:
            FFmpeg command as list of strings.
        """
        pass

    @abstractmethod
    def get_temp_directory(self, project_name: str, timestamp: str) -> Path:
        """
        Get temporary directory for recording files.

        Args:
            project_name: Name of the project.
            timestamp: ISO format timestamp.

        Returns:
            Path to temporary folder.
        """
        pass
