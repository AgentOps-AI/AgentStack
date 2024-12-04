"""
Methods for interacting with framework-specific features.

Each framework should have a module in the `frameworks` package which defines the following methods:

- `ENTRYPOINT`: Path: Relative path to the entrypoint file for the framework
- `validate_project(framework: str, path: Optional[Path] = None) -> None`: Validate that a project is ready to run.
       Raises a `ValidationError` if the project is not valid.
- `add_tool(framework: str, path: Optional[Path] = None) -> None`: Add a tool to the framework.
- `remove_tool(framework: str, path: Optional[Path] = None) -> None`: Remove a tool from the framework.
- `add_agent(framework: str, path: Optional[Path] = None) -> None`: Add an agent to the framework.
- `remove_agent(framework: str, path: Optional[Path] = None) -> None`: Remove an agent from the framework.
- `add_input(framework: str, path: Optional[Path] = None) -> None`: Add an input to the framework.
- `remove_input(framework: str, path: Optional[Path] = None) -> None`: Remove an input from the framework.
"""
from typing import TYPE_CHECKING, Optional
from importlib import import_module
from pathlib import Path
from agentstack import ValidationError
from agentstack.tools import ToolConfig


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

def get_entrypoint_path(framework: str, path: Optional[Path] = None) -> Path:
    """
    Get the path to the entrypoint file for a framework.
    """
    if not path: path = Path()
    return path/get_framework_module(framework).ENTRYPOINT

def validate_project(framework: str, path: Optional[Path] = None):
    """
    Run the framework specific project validation.
    """
    return get_framework_module(framework).validate_project(path)

def add_tool(framework: str, tool: ToolConfig, agent: str, path: Optional[Path] = None):
    """
    Add a tool to the framework. 
    
    The tool will have aready been installed in the user's application and have
    all dependencies installed. We're just handling code generation here.
    """
    return get_framework_module(framework).add_tool(tool, agent, path)

def remove_tool(framework: str, tool: ToolConfig, agent: str, path: Optional[Path] = None):
    """
    Remove a tool from the framework.
    """
    return get_framework_module(framework).remove_tool(tool, agent, path)

def get_agent_names(framework: str, path: Optional[Path] = None) -> list[str]:
    """
    Get a list of agent names from the framework.
    """
    return get_framework_module(framework).get_agent_names(path)

def add_agent(framework: str, path: Optional[Path] = None):
    """
    Add an agent to the framework.
    """
    return get_framework_module(framework).add_agent(path)

def remove_agent(framework: str, path: Optional[Path] = None):
    """
    Remove an agent from the framework.
    """
    return get_framework_module(framework).remove_agent(path)

def add_input(framework: str, path: Optional[Path] = None):
    """
    Add an input to the framework.
    """
    return get_framework_module(framework).add_input(path)

def remove_input(framework: str, path: Optional[Path] = None):
    """
    Remove an input from the framework.
    """
    return get_framework_module(framework).remove_input(path)

