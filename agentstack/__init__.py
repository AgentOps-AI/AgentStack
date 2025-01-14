"""
This it the beginning of the agentstack public API.

Methods that have been imported into this file are expected to be used by the
end user inside of their project.
"""

from typing import Callable
from pathlib import Path
from agentstack import conf
from agentstack.utils import get_framework
from agentstack.inputs import get_inputs
from agentstack import frameworks

___all___ = [
    "conf",
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
