"""
Audio device detection service.

This module provides functionality to detect available audio input devices
using the platform-specific service abstraction.

Available methods:
- list_audio_devices(): Returns a list of available audio device names.

Note: Requires FFmpeg to be installed and available in PATH.
"""
from .platform import get_platform_service


def list_audio_devices() -> list[str]:
    """
    List all available audio input devices.

    Returns:
        List of audio device names/identifiers (platform-specific format).

    Raises:
        RuntimeError: If unable to detect devices.
        NotImplementedError: If current platform is not supported.
    """
    platform_service = get_platform_service()
    return platform_service.list_audio_devices()
