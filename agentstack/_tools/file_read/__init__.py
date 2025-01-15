"""
Framework-agnostic implementation of file reading functionality.
"""

from typing import Optional
from pathlib import Path


def read_file(file_path: str) -> str:
    """Read contents of a file at the given path.

    Args:
        file_path: Path to the file to read

    Returns:
        str: The contents of the file as a string

    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be accessed
        Exception: For other file reading errors
    """
    try:
        path = Path(file_path).resolve()
        if not path.exists():
            return f"Error: File not found at path {file_path}"
        if not path.is_file():
            return f"Error: Path {file_path} is not a file"

        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except (FileNotFoundError, PermissionError, Exception) as e:
        return f"Failed to read file {file_path}. Error: {str(e)}"
