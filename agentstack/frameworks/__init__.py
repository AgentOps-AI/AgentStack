"""
Methods for interacting with framework-specific features.

Each framework should have a module in the `frameworks` package which defines the following methods:

- `ENTRYPOINT`: Path: Relative path to the entrypoint file for the framework
- `validate_project(path: Optional[Path] = None) -> None`: Validate that a project is ready to run.
       Raises a `ValidationError` if the project is not valid.
"""
from typing import Optional
from importlib import import_module
from pathlib import Path


CREWAI = 'crewai'
SUPPORTED_FRAMEWORKS = [CREWAI, ]

def get_framework_module(framework: str) -> import_module:
    """
    Get the module for a framework.
    """
    if framework == CREWAI:
        from . import crewai
        return crewai
    else:
        raise ValueError(f"Framework {framework} not supported")

def get_entrypoint_path(framework: str) -> Path:
    """
    Get the path to the entrypoint file for a framework.
    """
    return get_framework_module(framework).ENTRYPOINT

class ValidationError(Exception): pass

def validate_project(framework: str, path: Optional[Path] = None) -> None:
    """
    Run the framework specific project validation.
    """
    return get_framework_module(framework).validate_project(path)

