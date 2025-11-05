"""
Project persistence service.

This module provides functionality to save and load project configurations
to/from JSON files.

Available methods:
- save_project(config, filepath): Save project configuration to JSON file.
- load_project(filepath): Load project configuration from JSON file.

Note: Project files are stored in JSON format.
"""
import json
from pathlib import Path
from models.project import ProjectConfig


def save_project(config: ProjectConfig, filepath: str):
    """
    Save project configuration to a JSON file.

    Args:
        config: Project configuration to save.
        filepath: Path to save the project file.

    Raises:
        IOError: If file cannot be written.
    """
    file_path = Path(filepath)

    with file_path.open('w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def load_project(filepath: str) -> ProjectConfig:
    """
    Load project configuration from a JSON file.

    Args:
        filepath: Path to the project file.

    Returns:
        Loaded project configuration.

    Raises:
        FileNotFoundError: If file does not exist.
        json.JSONDecodeError: If file is not valid JSON.
    """
    file_path = Path(filepath)

    if not file_path.exists():
        raise FileNotFoundError(f"Project file not found: {filepath}")

    with file_path.open('r', encoding='utf-8') as f:
        data = json.load(f)

    return data
