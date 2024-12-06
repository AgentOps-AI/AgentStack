"""
Methods for interacting with framework-specific features.

Each framework should have a module in the `frameworks` package which defines the 
following methods:

`ENTRYPOINT`: Path: 
    Relative path to the entrypoint file for the framework in the user's project.
    ie. `src/crewai.py`

`validate_project(path: Optional[Path] = None) -> None`:
    Validate that a user's project is ready to run.
    Raises a `ValidationError` if the project is not valid.

`add_tool(tool: ToolConfig, agent_name: str, path: Optional[Path] = None) -> None`:
    Add a tool to an agent in the user's project.

`remove_tool(tool: ToolConfig, agent_name: str, path: Optional[Path] = None) -> None`:
    Remove a tool from an agent in user's project.

`get_agent_names(path: Optional[Path] = None) -> list[str]`:
    Get a list of agent names in the user's project.

`add_agent(agent: AgentConfig, path: Optional[Path] = None) -> None`:
    Add an agent to the user's project.

`add_task(task: TaskConfig, path: Optional[Path] = None) -> None`:
    Add a task to the user's project.
"""
from typing import Optional, Protocol
from types import ModuleType
from importlib import import_module
from pathlib import Path
from agentstack import ValidationError
from agentstack.tools import ToolConfig
from agentstack.agents import AgentConfig
from agentstack.tasks import TaskConfig


CREWAI = 'crewai'
SUPPORTED_FRAMEWORKS = [CREWAI, ]

class FrameworkModule(Protocol):
    ENTRYPOINT: Path

    def validate_project(self, path: Optional[Path] = None) -> None:
        ...

    def add_tool(self, tool: ToolConfig, agent_name: str, path: Optional[Path] = None) -> None:
        ...

    def remove_tool(self, tool: ToolConfig, agent_name: str, path: Optional[Path] = None) -> None:
        ...

    def get_agent_names(self, path: Optional[Path] = None) -> list[str]:
        ...

    def add_agent(self, agent: AgentConfig, path: Optional[Path] = None) -> None:
        ...

    def add_task(self, task: TaskConfig, path: Optional[Path] = None) -> None:
        ...


def get_framework_module(framework: str) -> FrameworkModule:
    """
    Get the module for a framework.
    """
    try:
        return import_module(f".{framework}", package=__package__)
    except ImportError:
        raise Exception(f"Framework {framework} could not be imported.")

def get_entrypoint_path(framework: str, path: Optional[Path] = None) -> Path:
    """
    Get the path to the entrypoint file for a framework.
    """
    if path is None:
        path = Path()
    return path / get_framework_module(framework).ENTRYPOINT

def validate_project(framework: str, path: Optional[Path] = None):
    """
    Validate that the user's project is ready to run.
    """
    return get_framework_module(framework).validate_project(path)

def add_tool(framework: str, tool: ToolConfig, agent_name: str, path: Optional[Path] = None):
    """
    Add a tool to the user's project. 
    The tool will have aready been installed in the user's application and have
    all dependencies installed. We're just handling code generation here.
    """
    return get_framework_module(framework).add_tool(tool, agent_name, path)

def remove_tool(framework: str, tool: ToolConfig, agent_name: str, path: Optional[Path] = None):
    """
    Remove a tool from the user's project.
    """
    return get_framework_module(framework).remove_tool(tool, agent_name, path)

def get_agent_names(framework: str, path: Optional[Path] = None) -> list[str]:
    """
    Get a list of agent names in the user's project.
    """
    return get_framework_module(framework).get_agent_names(path)

def add_agent(framework: str, agent: AgentConfig, path: Optional[Path] = None):
    """
    Add an agent to the user's project.
    """
    return get_framework_module(framework).add_agent(agent, path)

def add_task(framework: str, task: TaskConfig, path: Optional[Path] = None):
    """
    Add a task to the user's project.
    """
    return get_framework_module(framework).add_task(task, path)

