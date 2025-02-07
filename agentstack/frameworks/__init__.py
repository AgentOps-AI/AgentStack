from typing import TYPE_CHECKING, Optional, Protocol, Callable
from types import ModuleType
from importlib import import_module
from pathlib import Path
from agentstack import conf
from agentstack.exceptions import ValidationError
from agentstack.utils import get_framework
from agentstack.agents import AgentConfig, get_all_agent_names
from agentstack.tasks import TaskConfig, get_all_task_names
from agentstack._tools import ToolConfig
from agentstack import graph

if TYPE_CHECKING:
    from agentstack.generation import InsertionPoint


CREWAI = 'crewai'
LANGGRAPH = 'langgraph'
OPENAI_SWARM = 'openai_swarm'
SUPPORTED_FRAMEWORKS = [
    CREWAI,
    LANGGRAPH,
    OPENAI_SWARM,
]
DEFAULT_FRAMEWORK = CREWAI


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

    def wrap_tool(self, tool_func: Callable) -> Callable:
        """
        Wrap a tool function with framework-specific functionality.
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
    framework = get_framework()
    entrypoint_path = get_entrypoint_path(framework)
    _module = get_framework_module(framework)
    
    # Run framework-specific validation
    _module.validate_project()
    
    # Verify that agents defined in agents.yaml are present in the codebase
    agent_method_names = _module.get_agent_method_names()
    for agent_name in get_all_agent_names():
        if agent_name not in agent_method_names:
            raise ValidationError(
                f"Agent `{agent_name}` is defined in agents.yaml but not in {entrypoint_path}"
            )

    # Verify that tasks defined in tasks.yaml are present in the codebase
    task_method_names = _module.get_task_method_names()
    for task_name in get_all_task_names():
        if task_name not in task_method_names:
            raise ValidationError(
                f"Task `{task_name}` is defined in tasks.yaml but not in {entrypoint_path}"
            )


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
    # TODO: remove after agentops fixes their issue
    # wrap method with agentops tool event
    def wrap_method(method: Callable) -> Callable:
        from inspect import signature
        
        original_signature = signature(method)
        def wrapped_method(*args, **kwargs):
            import agentops
            tool_event = agentops.ToolEvent(method.__name__)
            result = method(*args, **kwargs)
            agentops.record(tool_event)
            return result

        # Preserve all original attributes
        wrapped_method.__name__ = method.__name__
        wrapped_method.__doc__ = method.__doc__
        wrapped_method.__module__ = method.__module__
        wrapped_method.__qualname__ = method.__qualname__
        wrapped_method.__annotations__ = getattr(method, '__annotations__', {})
        wrapped_method.__signature__ = original_signature  # type: ignore
        return wrapped_method

    tool_funcs = []
    tool_config = ToolConfig.from_tool_name(tool_name)
    for tool_func_name in tool_config.tools:
        tool_func = getattr(tool_config.module, tool_func_name)

        assert callable(tool_func), f"Tool function {tool_func_name} is not callable."
        assert tool_func.__doc__, f"Tool function {tool_func_name} is missing a docstring."

        # First wrap with agentops
        agentops_wrapped = wrap_method(tool_func)
        # Then apply framework decorators
        framework_wrapped = get_framework_module(get_framework()).wrap_tool(agentops_wrapped)
        tool_funcs.append(framework_wrapped)

    return tool_funcs


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
