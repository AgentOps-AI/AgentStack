"""
This it the beginning of the agentstack public API.

Methods that have been imported into this file are expected to be used by the
end user inside their project.
"""

from typing import Callable
from pathlib import Path
from agentstack import conf
from agentstack.utils import get_framework
from agentstack.agents import get_agent, get_all_agents, get_all_agent_names
from agentstack.tasks import get_task, get_all_tasks, get_all_task_names
from agentstack.inputs import get_inputs
from agentstack import frameworks

___all___ = [
    "conf", 
    "agent", 
    "task", 
    "tools", 
    "get_tags", 
    "get_framework", 
    "get_agent", 
    "get_all_agents",
    "get_all_agent_names",
    "get_task", 
    "get_all_tasks",
    "get_all_task_names",
    "get_inputs", 
]

def agent(func):
    """
    The `agent` decorator is used to mark a method that implements an Agent. 
    """
    def wrap(*args, **kwargs):
        """Does not alter the function's behavior; this is just a marker."""
        return func(*args, **kwargs)
    return wrap


def task(func):
    """
    The `task` decorator is used to mark a method that implements a Task.
    """
    def wrap(*args, **kwargs):
        """Does not alter the function's behavior; this is just a marker."""
        return func(*args, **kwargs)
    return wrap


def get_tags() -> list[str]:
    """
    Get a list of tags relevant to the user's project.
    """
    return ['agentstack', get_framework(), *conf.get_installed_tools()]


class ToolLoader:
    """
    Provides the public interface for accessing tools, wrapped in the
    framework-specific callable format.

    Get a tool's callables by name with `agentstack.tools[tool_name]`
    Include them in your agent's tool list with `tools = [*agentstack.tools[tool_name], ]`
    """

    def __getitem__(self, tool_name: str) -> list[Callable]:
        return frameworks.get_tool_callables(tool_name)

tools = ToolLoader()
