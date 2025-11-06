"""
Configuration service.

This module provides functionality to manage user configuration settings
stored in ~/.tutorialRecording/config.json

Available methods:
- load_config(): Load configuration from disk.
- save_config(config): Save configuration to disk.
- get_default_config(): Get default configuration values.
- update_config(updates): Update configuration with key-value pairs.
- update_export_path(path): Update export path.
- update_default_resolution(resolution): Update default resolution.

Configuration keys:
- export_path: Last selected export destination folder.
- default_resolution: Last used resolution (e.g., "1920x1080").
- permissions_warning_shown: Whether permissions warning was shown (bool).
"""
import json
from pathlib import Path
from typing import Dict, Optional


def _get_config_dir() -> Path:
    """
    Get the configuration directory path.

    Returns:
        Path to ~/.tutorialRecording directory.
    """
    config_dir = Path.home() / ".tutorialRecording"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def _get_config_file() -> Path:
    """
    Get the configuration file path.

    Returns:
        Path to config.json file.
    """
    return _get_config_dir() / "config.json"


def get_default_config() -> Dict:
    """
    Get default configuration values.

    Returns:
        Dictionary with default configuration.
    """
    return {
        "export_path": None,
        "default_resolution": "1920x1080"
    }


def load_config() -> Dict:
    """
    Load configuration from disk.

    Returns:
        Dictionary with configuration values. Returns defaults if file doesn't exist.
    """
    config_file = _get_config_file()

    if not config_file.exists():
        return get_default_config()

    try:
        with config_file.open('r', encoding='utf-8') as f:
            config = json.load(f)
            default = get_default_config()
            default.update(config)
            return default
    except (json.JSONDecodeError, IOError):
        return get_default_config()


def save_config(config: Dict):
    """
    Save configuration to disk.

    Args:
        config: Dictionary with configuration values.

    Raises:
        IOError: If unable to write configuration file.
    """
    config_file = _get_config_file()

    try:
        with config_file.open('w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except IOError as e:
        raise IOError(f"Failed to save configuration: {str(e)}")


def update_export_path(export_path: str):
    """
    Update the export path in configuration.

    Args:
        export_path: New export path to save.
    """
    config = load_config()
    config["export_path"] = export_path
    save_config(config)


def update_default_resolution(resolution: str):
    """
    Update the default resolution in configuration.

    Args:
        resolution: Resolution string (e.g., "1920x1080").
    """
    config = load_config()
    config["default_resolution"] = resolution
    save_config(config)


def update_config(updates: Dict):
    """
    Update configuration with provided key-value pairs.

    Args:
        updates: Dictionary with configuration updates.
    """
    config = load_config()
    config.update(updates)
    save_config(config)
