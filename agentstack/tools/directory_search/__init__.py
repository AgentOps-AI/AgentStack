"""Framework-agnostic directory search implementation using embedchain."""

from typing import Optional
from pathlib import Path
from embedchain.loaders.directory_loader import DirectoryLoader
import os


def search_directory(directory: str, query: str) -> str:
    """
    Search through files in a directory using embedchain's DirectoryLoader.

    Args:
        directory: Path to directory to search
        query: Search query to find relevant content

    Returns:
        str: Search results as a string
    """
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
    directory = os.getenv('DIRECTORY_SEARCH_TOOL_PATH')
    if not directory:
        raise ValueError("DIRECTORY_SEARCH_TOOL_PATH environment variable not set")
    return search_directory(directory, query)
