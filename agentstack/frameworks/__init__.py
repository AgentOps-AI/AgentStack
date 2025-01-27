from typing import Optional, Protocol, Callable
from types import ModuleType
from importlib import import_module
from pathlib import Path
from agentstack import conf
from agentstack.exceptions import ValidationError
from agentstack.utils import get_framework
from agentstack._tools import ToolConfig
from agentstack.agents import AgentConfig
from agentstack.tasks import TaskConfig


CREWAI = 'crewai'
SUPPORTED_FRAMEWORKS = [
    CREWAI,
]


class FrameworkModule(Protocol):
    """
    Protocol spec for a framework implementation module.
    """

    ENTRYPOINT: Path
    """
    Relative path to the entrypoint file for the framework in the user's project.
    ie. `src/crewai.py`
    """

    def validate_project(self) -> None:
        """
        Validate that a user's project is ready to run.
        Raises a `ValidationError` if the project is not valid.
        """
        ...

    def create_tool(self, tool_name: str) -> None:
        """
        Create a new custom tool in the user's project.
        Args:
            tool_name: Name of the tool to create (must be snake_case)
        """
        ...

    def get_tool_names(self) -> list[str]:
        """
        Get a list of tool names in the user's project.
        """
        ...

    def add_tool(self, tool: ToolConfig, agent_name: str) -> None:
        """
        Add a tool to an agent in the user's project.
        """
        ...

    def remove_tool(self, tool: ToolConfig, agent_name: str) -> None:
        """
        Remove a tool from an agent in user's project.
        """
        ...

    def get_tool_callables(self, tool_name: str) -> list[Callable]:
        """
        Get a tool by name and return it as a list of framework-native callables.
        """
        ...

    def get_agent_names(self) -> list[str]:
        """
        Get a list of agent names in the user's project.
        """
        ...

    def get_agent_tool_names(self, agent_name: str) -> list[str]:
        """
        Get a list of tool names in an agent in the user's project.
        """
        ...

    def add_agent(self, agent: AgentConfig) -> None:
        """
        Add an agent to the user's project.
        """
        ...

    def add_task(self, task: TaskConfig) -> None:
        """
        Add a task to the user's project.
        """
        ...

    def get_task_names(self) -> list[str]:
        """
        Get a list of task names in the user's project.
        """
        ...


def get_framework_module(framework: str) -> FrameworkModule:
    """
    Get the module for a framework.
    """
    try:
        return import_module(f".{framework}", package=__package__)
    except ImportError:
        raise Exception(f"Framework {framework} could not be imported.")


def get_entrypoint_path(framework: str) -> Path:
    """
    Get the path to the entrypoint file for a framework.
    """
    return conf.PATH / get_framework_module(framework).ENTRYPOINT


def validate_project():
    """
    Validate that the user's project is ready to run.
    """
    return get_framework_module(get_framework()).validate_project()


def add_tool(tool: ToolConfig, agent_name: str):
    """
    Add a tool to the user's project.
    The tool will have already been installed in the user's application and have
    all dependencies installed. We're just handling code generation here.
    """
    return get_framework_module(get_framework()).add_tool(tool, agent_name)


def remove_tool(tool: ToolConfig, agent_name: str):
    """
    Remove a tool from the user's project.
    """
    return get_framework_module(get_framework()).remove_tool(tool, agent_name)


def get_tool_callables(tool_name: str) -> list[Callable]:
    """
    Get a tool by name and return it as a list of framework-native callables.
    """
    return get_framework_module(get_framework()).get_tool_callables(tool_name)


def get_agent_names() -> list[str]:
    """
    Get a list of agent names in the user's project.
    """
    return get_framework_module(get_framework()).get_agent_names()


def get_agent_tool_names(agent_name: str) -> list[str]:
    """
    Get a list of tool names in the user's project.
    """
    return get_framework_module(get_framework()).get_agent_tool_names(agent_name)


def add_agent(agent: AgentConfig):
    """
    Add an agent to the user's project.
    """
    return get_framework_module(get_framework()).add_agent(agent)


def add_task(task: TaskConfig):
    """
    Add a task to the user's project.
    """
    return get_framework_module(get_framework()).add_task(task)


def get_task_names() -> list[str]:
    """
    Get a list of task names in the user's project.
    """
    return get_framework_module(get_framework()).get_task_names()


def create_tool(tool_name: str):
    """
    Create a new custom tool in the user's project.
    The tool will be created with a basic structure and configuration.
    """
    return get_framework_module(get_framework()).create_tool(tool_name)
