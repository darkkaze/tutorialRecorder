"""
Export service.

This module provides functionality to merge recorded audio and video files
into a final video with the selected layout using FFmpeg.

Available functions:
- export_video(project_folder, layout_name, progress_callback): Export merged video.
- open_folder_in_explorer(folder_path): Open folder in system file browser.

Note: Requires FFmpeg to be installed and available in PATH.
"""
import subprocess
import json
import platform
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime
from utils.ffmpeg_utils import get_ffmpeg_path


def export_video(
    project_folder: Path,
    layout_name: str,
    progress_callback: Optional[Callable[[int], None]] = None
) -> tuple[bool, str]:
    """
    Export merged video with selected layout.

    Args:
        project_folder: Path to project folder with recordings.
        layout_name: Name of selected layout.
        progress_callback: Optional callback for progress updates (0-100).

    Returns:
        Tuple of (success: bool, output_path or error_message: str).

    Raises:
        FileNotFoundError: If required project files not found.
        RuntimeError: If FFmpeg fails.
    """
    try:
        # Load metadata
        metadata_path = project_folder / "metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError("metadata.json not found in project folder")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Get project name
        project_name = metadata.get("project_name", "exported")

        # Check required files
        screen_file = project_folder / "screen.mp4"
        webcam_file = project_folder / "webcam.mp4"

        if not screen_file.exists():
            raise FileNotFoundError("screen.mp4 not found")
        if not webcam_file.exists():
            raise FileNotFoundError("webcam.mp4 not found")

        # Find all audio files
        audio_files = sorted(project_folder.glob("mic*.wav"))

        # Generate output filename
        layout_slug = layout_name.lower().replace(" ", "_")
        output_filename = f"{project_name}_{layout_slug}.mp4"
        output_path = project_folder / output_filename

        # Calculate total duration for progress
        total_duration = _get_video_duration(metadata)

        # Build FFmpeg command
        cmd = _build_ffmpeg_command(
            layout_name,
            screen_file,
            webcam_file,
            audio_files,
            output_path
        )

        # Log command for debugging
        print("FFmpeg command:", " ".join(cmd))

        # Execute FFmpeg with progress monitoring
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        # Collect output for error reporting
        output_lines = []

        # Monitor progress
        for line in process.stdout:
            output_lines.append(line)
            print(line.strip())  # Debug output

            if progress_callback and total_duration:
                progress = _parse_ffmpeg_progress(line, total_duration)
                if progress is not None:
                    progress_callback(progress)

        process.wait()

        if process.returncode != 0:
            # Include last 20 lines of output in error message
            error_context = "\n".join(output_lines[-20:])
            raise RuntimeError(
                f"FFmpeg failed with return code {process.returncode}\n\n"
                f"Last output:\n{error_context}"
            )

        return True, str(output_path)

    except Exception as e:
        return False, str(e)


def _get_video_duration(metadata: dict) -> Optional[float]:
    """
    Calculate total video duration from metadata timestamps.

    Args:
        metadata: Project metadata dictionary.

    Returns:
        Duration in seconds, or None if timestamps not available.
    """
    try:
        start_str = metadata.get("start_timestamp")
        stop_str = metadata.get("stop_timestamp")

        if not start_str or not stop_str:
            return None

        start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        stop = datetime.fromisoformat(stop_str.replace('Z', '+00:00'))

        duration = (stop - start).total_seconds()
        return max(duration, 1.0)  # At least 1 second

    except Exception:
        return None


def _parse_ffmpeg_progress(line: str, total_duration: float) -> Optional[int]:
    """
    Parse FFmpeg progress output line.

    Args:
        line: Line from FFmpeg stdout.
        total_duration: Total video duration in seconds.

    Returns:
        Progress percentage (0-100), or None if line doesn't contain progress.
    """
    # FFmpeg progress format: out_time_ms=12345678
    if "out_time_ms=" in line:
        try:
            # Extract time in microseconds
            time_str = line.split("out_time_ms=")[1].strip()
            time_ms = int(time_str)
            time_seconds = time_ms / 1_000_000

            # Calculate percentage
            progress = int((time_seconds / total_duration) * 100)
            return min(progress, 100)

        except (ValueError, IndexError):
            pass

    return None


def _build_ffmpeg_command(
    layout_name: str,
    screen_file: Path,
    webcam_file: Path,
    audio_files: list[Path],
    output_path: Path
) -> list[str]:
    """
    Build FFmpeg command based on layout.

    Args:
        layout_name: Name of selected layout.
        screen_file: Path to screen recording.
        webcam_file: Path to webcam recording.
        audio_files: List of audio file paths.
        output_path: Path for output file.

    Returns:
        FFmpeg command as list of strings.

    Raises:
        ValueError: If layout name is unknown.
    """
    # Base command
    cmd = [get_ffmpeg_path(), "-y"]  # -y to overwrite without asking

    # Add input files
    cmd.extend(["-i", str(screen_file)])
    cmd.extend(["-i", str(webcam_file)])

    for audio_file in audio_files:
        cmd.extend(["-i", str(audio_file)])

    # Build filter based on layout
    if layout_name == "Vertical Bottom":
        filter_complex = _build_vertical_bottom_filter(len(audio_files))
    elif layout_name == "Vertical Top":
        filter_complex = _build_vertical_top_filter(len(audio_files))
    elif layout_name == "Down Right":
        filter_complex = _build_horizontal_down_right_filter(len(audio_files))
    elif layout_name == "Down Left":
        filter_complex = _build_horizontal_down_left_filter(len(audio_files))
    elif layout_name == "Top Right":
        filter_complex = _build_horizontal_top_right_filter(len(audio_files))
    elif layout_name == "Top Left":
        filter_complex = _build_horizontal_top_left_filter(len(audio_files))
    else:
        raise ValueError(f"Unknown layout: {layout_name}")

    # Add filter complex
    cmd.extend(["-filter_complex", filter_complex])

    # Map output streams
    cmd.extend(["-map", "[v]", "-map", "[a]"])

    # Video codec settings
    cmd.extend([
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart"
    ])

    # Audio codec settings
    cmd.extend([
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest"  # Stop encoding when shortest stream ends
    ])

    # Progress output
    cmd.extend(["-progress", "pipe:1"])

    # Output file
    cmd.append(str(output_path))

    return cmd


def _build_vertical_bottom_filter(audio_count: int) -> str:
    """
    Build filter for Vertical Bottom layout (9:16, 1080x1920).
    Screen on top, webcam on bottom.

    Args:
        audio_count: Number of audio tracks.

    Returns:
        FFmpeg filter_complex string.
    """
    # Screen: scale to width 1080, maintain aspect ratio
    # Webcam: scale to width 1080, crop to fill remaining space
    # Stack vertically

    # Calculate webcam crop height (assuming screen takes ~1080px height)
    # Total height: 1920, Screen: ~1080, Webcam: ~840

    filter_parts = []

    # Screen: scale to 1080 width (height maintains aspect ratio, ~600-1080px)
    filter_parts.append("[0:v]scale=1080:-1[screen]")

    # Webcam: scale to cover 1080x1200 then crop centered (extra height to compensate)
    filter_parts.append("[1:v]scale=1080:1200:force_original_aspect_ratio=increase,crop=1080:1200[webcam_tall]")

    # Stack vertically (will be taller than 1760)
    filter_parts.append("[screen][webcam_tall]vstack[stacked_tall]")

    # Crop stack centered to exactly 1760 height (removes excess from webcam)
    filter_parts.append("[stacked_tall]crop=1080:1760[stacked]")

    # Duplicate: one for content, one for blur background
    filter_parts.append("[stacked]split[content][blur_src]")

    # Create blurred background: scale to 1920 height and apply blur
    filter_parts.append("[blur_src]scale=1080:1920,boxblur=30:30[blurred]")

    # Overlay content at y=80 (80px blur top + 1760px content + 80px blur bottom)
    filter_parts.append("[blurred][content]overlay=0:80[v]")

    # Mix audio
    if audio_count > 0:
        audio_inputs = "".join([f"[{i+2}:a]" for i in range(audio_count)])
        filter_parts.append(f"{audio_inputs}amix=inputs={audio_count}:duration=longest[a]")
    else:
        # Create silent audio matching video duration
        filter_parts.append("anullsrc=r=44100:cl=stereo[a]")

    return ";".join(filter_parts)


def _build_vertical_top_filter(audio_count: int) -> str:
    """
    Build filter for Vertical Top layout (9:16, 1080x1920).
    Webcam on top, screen on bottom.

    Args:
        audio_count: Number of audio tracks.

    Returns:
        FFmpeg filter_complex string.
    """
    filter_parts = []

    # Webcam: scale to cover 1080x1200 then crop centered (extra height to compensate)
    filter_parts.append("[1:v]scale=1080:1200:force_original_aspect_ratio=increase,crop=1080:1200[webcam_tall]")

    # Screen: scale to 1080 width (height maintains aspect ratio, ~600-1080px)
    filter_parts.append("[0:v]scale=1080:-1[screen]")

    # Stack vertically (webcam top, screen bottom - will be taller than 1760)
    filter_parts.append("[webcam_tall][screen]vstack[stacked_tall]")

    # Crop stack centered to exactly 1760 height (removes excess from webcam)
    filter_parts.append("[stacked_tall]crop=1080:1760[stacked]")

    # Duplicate: one for content, one for blur background
    filter_parts.append("[stacked]split[content][blur_src]")

    # Create blurred background: scale to 1920 height and apply blur
    filter_parts.append("[blur_src]scale=1080:1920,boxblur=30:30[blurred]")

    # Overlay content at y=80 (80px blur top + 1760px content + 80px blur bottom)
    filter_parts.append("[blurred][content]overlay=0:80[v]")

    # Mix audio
    if audio_count > 0:
        audio_inputs = "".join([f"[{i+2}:a]" for i in range(audio_count)])
        filter_parts.append(f"{audio_inputs}amix=inputs={audio_count}:duration=longest[a]")
    else:
        filter_parts.append("anullsrc=r=44100:cl=stereo[a]")

    return ";".join(filter_parts)


def _build_horizontal_down_right_filter(audio_count: int) -> str:
    """
    Build filter for Down Right layout (16:9, 1920x1080).
    Screen full size, webcam in bottom-right corner (25% width = 480x270).

    Args:
        audio_count: Number of audio tracks.

    Returns:
        FFmpeg filter_complex string.
    """
    filter_parts = []

    # Pad screen to 1920x1080 if needed (add black bars)
    filter_parts.append("[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black[screen]")

    # Scale webcam to 480x270 (25% of 1920 width)
    filter_parts.append("[1:v]scale=480:270:force_original_aspect_ratio=increase,crop=480:270[webcam]")

    # Overlay webcam in bottom-right corner (with 20px padding)
    filter_parts.append("[screen][webcam]overlay=W-w-20:H-h-20[v]")

    # Mix audio
    if audio_count > 0:
        audio_inputs = "".join([f"[{i+2}:a]" for i in range(audio_count)])
        filter_parts.append(f"{audio_inputs}amix=inputs={audio_count}:duration=longest[a]")
    else:
        filter_parts.append("anullsrc=r=44100:cl=stereo[a]")

    return ";".join(filter_parts)


def _build_horizontal_down_left_filter(audio_count: int) -> str:
    """
    Build filter for Down Left layout (16:9, 1920x1080).
    Screen full size, webcam in bottom-left corner.

    Args:
        audio_count: Number of audio tracks.

    Returns:
        FFmpeg filter_complex string.
    """
    filter_parts = []

    filter_parts.append("[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black[screen]")
    filter_parts.append("[1:v]scale=480:270:force_original_aspect_ratio=increase,crop=480:270[webcam]")

    # Overlay in bottom-left corner
    filter_parts.append("[screen][webcam]overlay=20:H-h-20[v]")

    if audio_count > 0:
        audio_inputs = "".join([f"[{i+2}:a]" for i in range(audio_count)])
        filter_parts.append(f"{audio_inputs}amix=inputs={audio_count}:duration=longest[a]")
    else:
        filter_parts.append("anullsrc=r=44100:cl=stereo[a]")

    return ";".join(filter_parts)


def _build_horizontal_top_right_filter(audio_count: int) -> str:
    """
    Build filter for Top Right layout (16:9, 1920x1080).
    Screen full size, webcam in top-right corner.

    Args:
        audio_count: Number of audio tracks.

    Returns:
        FFmpeg filter_complex string.
    """
    filter_parts = []

    filter_parts.append("[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black[screen]")
    filter_parts.append("[1:v]scale=480:270:force_original_aspect_ratio=increase,crop=480:270[webcam]")

    # Overlay in top-right corner
    filter_parts.append("[screen][webcam]overlay=W-w-20:20[v]")

    if audio_count > 0:
        audio_inputs = "".join([f"[{i+2}:a]" for i in range(audio_count)])
        filter_parts.append(f"{audio_inputs}amix=inputs={audio_count}:duration=longest[a]")
    else:
        filter_parts.append("anullsrc=r=44100:cl=stereo[a]")

    return ";".join(filter_parts)


def _build_horizontal_top_left_filter(audio_count: int) -> str:
    """
    Build filter for Top Left layout (16:9, 1920x1080).
    Screen full size, webcam in top-left corner.

    Args:
        audio_count: Number of audio tracks.

    Returns:
        FFmpeg filter_complex string.
    """
    filter_parts = []

    filter_parts.append("[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black[screen]")
    filter_parts.append("[1:v]scale=480:270:force_original_aspect_ratio=increase,crop=480:270[webcam]")

    # Overlay in top-left corner
    filter_parts.append("[screen][webcam]overlay=20:20[v]")

    if audio_count > 0:
        audio_inputs = "".join([f"[{i+2}:a]" for i in range(audio_count)])
        filter_parts.append(f"{audio_inputs}amix=inputs={audio_count}:duration=longest[a]")
    else:
        filter_parts.append("[0:a]anull[a]")

    return ";".join(filter_parts)


def open_folder_in_explorer(folder_path: Path):
    """
    Open folder in system file browser.

    Args:
        folder_path: Path to folder to open.
    """
    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(folder_path)], check=True)
        elif system == "Windows":
            subprocess.run(["explorer", str(folder_path)], check=True)
        else:  # Linux and others
            subprocess.run(["xdg-open", str(folder_path)], check=True)
    except Exception as e:
        print(f"Failed to open folder: {e}")
