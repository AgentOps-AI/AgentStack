"""
Framework-agnostic implementation of file reading functionality.
"""

from typing import Optional
from pathlib import Path
from fnmatch import fnmatch
from agentstack import tools


def _is_path_allowed(path: Path, allowed_patterns: list[str]) -> bool:
    """Check if the given path matches any of the allowed patterns."""
    return any(fnmatch(str(path), pattern) for pattern in allowed_patterns)


def read_file(file_path: str) -> str:
    """
    Read the contents of a file at the given path.

    Args:
        file_path: Path to the file to read

    Returns:
        str: The contents of the file as a string or a description of the error
    """
    permissions = tools.get_permissions(read_file)
    path = Path(file_path).resolve()
    
    if not permissions.READ:
        return "User has not granted read permission."

    if permissions.allowed_dirs:
        if not _is_path_allowed(path, permissions.allowed_dirs):
            return (
                f"Error: Access to file {file_path} is not allowed. "
                f"Allowed directories: {permissions.allowed_dirs}"
            )

    if permissions.allowed_extensions:
        if not _is_path_allowed(path.name, permissions.allowed_extensions):
            return (
                f"Error: File extension of {file_path} is not allowed. "
                f"Allowed extensions: {permissions.allowed_extensions}"
            )

    if not path.exists():
        return f"Error: File not found at path {file_path}"
    if not path.is_file():
        return f"Error: Path {file_path} is not a file"
    
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        return f"Failed to read file {file_path}. Error: {str(e)}"
