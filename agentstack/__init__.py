"""
This it the beginning of the agentstack public API.

Methods that have been imported into this file are expected to be used by the
end user inside of their project.
"""

from typing import Optional, Callable, Any
from functools import wraps
from pathlib import Path
from agentstack import conf
from agentstack.utils import get_framework
from agentstack.inputs import get_inputs
from agentstack import frameworks

___all___ = [
    "conf",
    "extra",
    "tools",
    "get_tags",
    "get_framework",
    "get_inputs",
]


def get_tags() -> list[str]:
    """
    Get a list of tags relevant to the user's project.
    """
    return ['agentstack', get_framework(), *conf.get_installed_tools()]


def agent(agent_name: Optional[str] = None):
    """
    The `agent` decorator.
    This will pass kwargs needed when instantiating an agent in your framework.
    """

    def decorator(func):
        nonlocal agent_name
        if agent_name is None:
            agent_name = func.__name__

        @wraps(func)
        def wrapper(**kwargs):
            return func(**frameworks.get_agent_decorator_kwargs(agent_name))

        return wrapper

    if callable(agent_name):
        # This handles the case when the decorator is used without parentheses
        f = agent_name
        agent_name = None
        return decorator(f)
    
    return decorator


def task(task_name: Optional[str] = None):
    """
    The `task` decorator.
    This will pass kwargs needed when instantiating a task in your framework.
    """

    def decorator(func):
        nonlocal task_name
        if task_name is None:
            task_name = func.__name__

        @wraps(func)
        def wrapper(**kwargs):
            return func(**frameworks.get_task_decorator_kwargs(task_name))

        return wrapper

    if callable(task_name):
        # This handles the case when the decorator is used without parentheses
        f = task_name
        task_name = None
        return decorator(f)
    
    return decorator


class ConfExtraLoader:
    """
    Provides the public interface for accessing the `extra` vars in the project's
    agentstack.json file.
    """

    def __getitem__(self, name: str) -> Any:
        conf_file = conf.ConfigFile()
        return conf_file.extra.get(name) if conf_file.extra else None


extra = ConfExtraLoader()


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
