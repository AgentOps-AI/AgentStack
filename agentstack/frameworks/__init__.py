from typing import TYPE_CHECKING, Optional, Protocol, Callable
from types import ModuleType
from importlib import import_module
from pathlib import Path
from agentstack import conf
from agentstack.exceptions import ValidationError
from agentstack.utils import get_framework
from agentstack._tools import ToolConfig
from agentstack import graph
if TYPE_CHECKING:
    from agentstack.generation import InsertionPoint
    from agentstack.agents import AgentConfig
    from agentstack.tasks import TaskConfig


CREWAI = 'crewai'
LANGGRAPH = 'langgraph'
SUPPORTED_FRAMEWORKS = [
    CREWAI,
    LANGGRAPH,
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

    def parse_llm(self, llm: str) -> tuple[str, str]:
        """
        Parse a language model string into a provider and model.
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

    def get_agent_method_names(self) -> list[str]:
        """
        Get a list of agent names in the user's project.
        """
        ...

    def get_agent_tool_names(self, agent_name: str) -> list[str]:
        """
        Get a list of tool names in an agent in the user's project.
        """
        ...

    def add_agent(self, agent: 'AgentConfig', position: Optional['InsertionPoint'] = None) -> None:
        """
        Add an agent to the user's project.
        """
        ...

    def add_task(self, task: 'TaskConfig', position: Optional['InsertionPoint'] = None) -> None:
        """
        Add a task to the user's project.
        """
        ...

    def get_task_method_names(self) -> list[str]:
        """
        Get a list of task names in the user's project.
        """
        ...
    
    def get_graph(self) -> list[graph.Edge]:
        """
        Get the graph of the user's project.
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


def parse_llm(llm: str) -> tuple[str, str]:
    """
    Parse a language model string into a provider and model.
    """
    return get_framework_module(get_framework()).parse_llm(llm)


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


def get_agent_method_names() -> list[str]:
    """
    Get a list of agent names in the user's project.
    """
    return get_framework_module(get_framework()).get_agent_method_names()


def get_agent_tool_names(agent_name: str) -> list[str]:
    """
    Get a list of tool names in the user's project.
    """
    return get_framework_module(get_framework()).get_agent_tool_names(agent_name)


def add_agent(agent: 'AgentConfig', position: Optional['InsertionPoint'] = None):
    """
    Add an agent to the user's project.
    """
    framework = get_framework()
    if agent.name in get_agent_method_names():
        raise ValidationError(f"Agent `{agent.name}` already exists in {get_entrypoint_path(framework)}")
    return get_framework_module(framework).add_agent(agent, position)


def add_task(task: 'TaskConfig', position: Optional['InsertionPoint'] = None):
    """
    Add a task to the user's project.
    """
    framework = get_framework()
    if task.name in get_task_method_names():
        raise ValidationError(f"Task `{task.name}` already exists in {get_entrypoint_path(framework)}")
    return get_framework_module(framework).add_task(task, position)


def get_task_method_names() -> list[str]:
    """
    Get a list of task names in the user's project.
    """
    return get_framework_module(get_framework()).get_task_method_names()


def get_graph() -> list[graph.Edge]:
    """
    Get the graph of the user's project.
    """
    return get_framework_module(get_framework()).get_graph()

