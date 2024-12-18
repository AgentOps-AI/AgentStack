"""Framework-agnostic directory search implementation using embedchain."""
import os
from embedchain import DirectoryLoader

def search_directory(directory: str, query: str) -> str:
    """Search through files in a specified directory using embedchain's DirectoryLoader.

    Args:
        directory: Path to the directory to search
        query: Search query string

    Returns:
        str: Search results as a string
    """
    loader = DirectoryLoader(directory)
    results = loader.search(query)
    return str(results)

def search_fixed_directory(query: str) -> str:
    """Search through files in a preconfigured directory using embedchain's DirectoryLoader.

    Args:
        query: Search query string

    Returns:
        str: Search results as a string

    Raises:
        ValueError: If DIRECTORY_SEARCH_PATH environment variable is not set
    """
    directory = os.getenv("DIRECTORY_SEARCH_PATH")
    if not directory:
        raise ValueError("DIRECTORY_SEARCH_PATH environment variable must be set")
    return search_directory(directory, query)
