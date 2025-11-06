"""
FFmpeg utilities.

This module provides helper functions for FFmpeg integration.
"""
import sys
import os


def get_ffmpeg_path() -> str:
    """
    Get FFmpeg binary path (bundled or system).

    When running as PyInstaller bundle, returns path to bundled FFmpeg.
    When running from source, returns system FFmpeg command.

    Returns:
        Path to FFmpeg executable.
    """
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = sys._MEIPASS
        return os.path.join(base_path, 'ffmpeg')
    else:
        # Running normally, use system FFmpeg
        return 'ffmpeg'
