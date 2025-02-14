from enum import Enum
from .agent_generation import add_agent
from .task_generation import add_task
from .tool_generation import add_tool, create_tool, remove_tool
from .files import EnvFile, ProjectFile


class InsertionPoint(Enum):
    """
    Enum for specifying where to insert generated code.
    """

    BEGIN = 'begin'
    END = 'end'


