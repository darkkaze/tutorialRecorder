"""
Platform abstraction layer.

This module provides a factory to detect the current platform and return
the appropriate platform-specific service implementation.

Usage:
    from services.platform import get_platform_service

    platform_service = get_platform_service()
    devices = platform_service.list_audio_devices()
"""
import platform as platform_module
from .base import BasePlatformService
from .macos import MacOSPlatformService
from .windows import WindowsPlatformService
from .linux import LinuxPlatformService


_platform_service_instance = None


def get_platform_service() -> BasePlatformService:
    """
    Get the platform-specific service instance (singleton).

    Returns:
        Platform-specific service implementation.

    Raises:
        RuntimeError: If the current platform is not supported.
    """
    global _platform_service_instance

    if _platform_service_instance is not None:
        return _platform_service_instance

    system = platform_module.system()

    if system == "Darwin":
        _platform_service_instance = MacOSPlatformService()
    elif system == "Windows":
        _platform_service_instance = WindowsPlatformService()
    elif system == "Linux":
        _platform_service_instance = LinuxPlatformService()
    else:
        raise RuntimeError(f"Unsupported platform: {system}")

    return _platform_service_instance


__all__ = [
    "BasePlatformService",
    "get_platform_service",
    "MacOSPlatformService",
    "WindowsPlatformService",
    "LinuxPlatformService",
]
