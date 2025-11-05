"""
Project data models.

This module defines TypedDict structures for project configuration.
"""
from typing import TypedDict


class AudioInput(TypedDict):
    """Configuration for an audio input device."""
    device_name: str


class VideoInput(TypedDict):
    """Configuration for a video input device."""
    device_name: str
    source_type: str  # "webcam" or "screen"


class ScreenArea(TypedDict):
    """Screen capture area configuration."""
    x: int
    y: int
    width: int
    height: int
    aspect_ratio: str  # "16:9", "9:16", "4:3", "1:1", "free"


class ProjectConfig(TypedDict):
    """Complete project configuration."""
    name: str
    audio_inputs: list[AudioInput]
    video_inputs: list[VideoInput]
    screen_area: ScreenArea | None
