from typing import Optional, Any, Callable
from pathlib import Path
import ast
from agentstack import conf, log
from agentstack.exceptions import ValidationError
from agentstack.generation import InsertionPoint
from agentstack.frameworks import BaseEntrypointFile
from agentstack._tools import ToolConfig
from agentstack.tasks import TaskConfig
from agentstack.agents import AgentConfig
from agentstack.generation import asttools
from agentstack import graph

NAME: str = "LLama Index"
ENTRYPOINT: Path = Path('src/stack.py')


class LlamaIndexFile(BaseEntrypointFile):
    """
    Parses and manipulates the entrypoint file.
    All AST interactions should happen within the methods of this class.
    """
    base_class_pattern = r'\w+Stack$'
    agent_decorator_name: str = 'agent'
    task_decorator_name: str = 'task'
    
    def get_task_methods(self) -> list[ast.FunctionDef]:
        """A `task` method is a method decorated with `@task`."""
        pass

    def get_new_task_method(self, task: TaskConfig) -> str:
        """Get the content of a new task method. """
        pass

    def get_agent_methods(self) -> list[ast.FunctionDef]:
        """An `agent` method is a method decorated with `@agent`."""
        pass

    def get_new_agent_method(self, agent: AgentConfig) -> str:
        """Get the content of a new agent method."""
        pass

    def get_agent_tools(self, agent_name: str) -> ast.List:
        """Get the tools used by an agent as AST nodes."""
        pass

    def get_agent_tool_names(self, agent_name: str) -> list[str]:
        """Get a list of all tools used by the agent."""
        pass

    def add_agent_tools(self, agent_name: str, tool: ToolConfig) -> None:
        """Add new tools to be used by an agent."""
        pass

    def remove_agent_tools(self, agent_name: str, tool: ToolConfig) -> None:
        """Remove tools from an agent belonging to `tool`."""
        pass


def get_entrypoint() -> LlamaIndexFile:
    """Get the entrypoint file."""
    return LlamaIndexFile(conf.PATH / ENTRYPOINT)


def validate_project() -> None:
    """
    Validate that the project is ready to run.
    Raises an `agentstack.ValidationError` if the project is not valid.
    """
    return  # No additional validation needed.


def parse_llm(llm: str) -> tuple[str, str]:
    """
    Parse the llm string into a tuple of `provider` and `model`.
    """
    provider, model = llm.split('/')
    return provider, model


def add_task(task: TaskConfig, position: Optional['InsertionPoint'] = None) -> None:
    """
    Add a task method to the entrypoint.
    """
    if position is not None:
        raise NotImplementedError(f"Task insertion points are not supported in {NAME}.")

    with get_entrypoint() as entrypoint:
        entrypoint.add_task_method(task)


def get_agent_tool_names(agent_name: str) -> list[Any]:
    """
    Get a list of tools used by an agent.
    """
    with get_entrypoint() as entrypoint:
        return entrypoint.get_agent_tool_names(agent_name)


def add_agent(agent: AgentConfig, position: Optional['InsertionPoint'] = None) -> None:
    """
    Add an agent method to the entrypoint.
    """
    if position is not None:
        raise NotImplementedError(f"Agent insertion points are not supported in {NAME}.")
    
    with get_entrypoint() as entrypoint:
        entrypoint.add_agent_method(agent)


def add_tool(tool: ToolConfig, agent_name: str):
    """
    Add a tool to the entrypoint for the specified agent.
    """
    with get_entrypoint() as entrypoint:
        entrypoint.add_agent_tools(agent_name, tool)


def remove_tool(tool: ToolConfig, agent_name: str):
    """
    Remove a tool from the entrypoint for the specified agent.
    """
    with get_entrypoint() as entrypoint:
        entrypoint.remove_agent_tools(agent_name, tool)


def wrap_tool(tool_func: Callable) -> Callable:
    """
    Wrap a tool function with framework-specific functionality.
    """
    try:
        # import happens at runtime to avoid including the framework as a base dependency.
        #from crewai.tools import tool as _framework_tool_decorator
        _framework_tool_decorator = lambda x: x
    except ImportError:
        raise ValidationError(f"Could not import framework. Is this an AgentStack {NAME} project?")
    
    return _framework_tool_decorator(tool_func)


def get_graph() -> list[graph.Edge]:
    """Get the graph of the user's project."""
    log.debug(f"{NAME} does not support graph generation.")
    return []

