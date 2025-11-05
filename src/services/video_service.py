"""
Video device detection service.

This module provides functionality to detect available video input devices
and screen capture sources using the platform-specific service abstraction.

Available methods:
- list_video_devices(): Returns a list of available video device names (webcams).
- get_screen_capture_source(): Returns the screen capture device identifier.

Note: Requires FFmpeg to be installed and available in PATH.
"""
from .platform import get_platform_service


def list_video_devices() -> list[str]:
    """
    List all available video input devices (webcams).

    Returns:
        List of video device names/identifiers (platform-specific format).

    Raises:
        RuntimeError: If unable to detect devices.
        NotImplementedError: If current platform is not supported.
    """
    platform_service = get_platform_service()
    return platform_service.list_video_devices()


def get_screen_capture_source() -> str:
    """
    Get the screen capture device identifier.

    Returns:
        Screen capture device identifier (platform-specific format).

    Raises:
        RuntimeError: If screen capture not available.
        NotImplementedError: If current platform is not supported.
    """
    platform_service = get_platform_service()
    return platform_service.get_screen_capture_device()
