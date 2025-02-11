"""Framework-agnostic directory search implementation using embedchain."""
import os
from typing import Optional
from pathlib import Path
from fnmatch import fnmatch
from agentstack import tools
from embedchain.loaders.directory_loader import DirectoryLoader


def _is_path_allowed(path: str, allowed_patterns: list[str]) -> bool:
    """Check if the given path matches any of the allowed patterns."""
    return any(fnmatch(path, pattern) for pattern in allowed_patterns)


def search_directory(directory: str, query: str) -> str:
    """
    Search through files in a directory using embedchain's DirectoryLoader.

    Args:
        directory: Path to directory to search
        query: Search query to find relevant content

    Returns:
        str: Search results as a string
    """
    permissions = tools.get_permissions(search_directory)
    if not permissions.READ:
        return "User has not granted read permission."
    
    if permissions.allowed_dirs:
        if not _is_path_allowed(directory, permissions.allowed_dirs):
            return (
                f"Error: Access to directory {directory} is not allowed. "
                f"Allowed directories: {permissions.allowed_dirs}"
            )
    
    loader = DirectoryLoader(config=dict(recursive=True))
    results = loader.search(directory, query)
    return str(results)


def search_fixed_directory(query: str) -> str:
    """
    Search through files in a preconfigured directory using embedchain's DirectoryLoader.
    Uses DIRECTORY_SEARCH_TOOL_PATH environment variable.

    Args:
        query: Search query to find relevant content

    Returns:
        str: Search results as a string

    Raises:
        ValueError: If DIRECTORY_SEARCH_TOOL_PATH environment variable is not set
    """
    
    permissions = tools.get_permissions(search_fixed_directory)
    if not permissions.READ:
        return "User has not granted read permission."
    
    directory = os.getenv('DIRECTORY_SEARCH_TOOL_PATH')
    if not directory:
        raise ValueError("DIRECTORY_SEARCH_TOOL_PATH environment variable not set")
    return search_directory(directory, query)
