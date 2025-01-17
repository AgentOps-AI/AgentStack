from typing import Optional
from enum import Enum
from .agent_generation import add_agent
from .task_generation import add_task
from .tool_generation import add_tool, remove_tool
from .files import EnvFile, ProjectFile


class InsertionPoint(Enum):
    """
    Enum for specifying where to insert generated code.
    """
    BEGIN = 'begin'
    END = 'end'


def parse_insertion_point(position: Optional[str]) -> Optional[InsertionPoint]:
    """
    Parse an insertion point CLI argument into an InsertionPoint enum.
    """
    if position is None:
        return None  # defer assumptions
    
    valid_positions = {x.value for x in InsertionPoint}
    if position not in valid_positions:
        raise ValueError(f"Position must be one of {','.join(valid_positions)}.")
    
    return next(x for x in InsertionPoint if x.value == position)

