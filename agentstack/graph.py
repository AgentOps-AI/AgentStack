from typing import Literal
from enum import Enum
import pydantic


class NodeType(Enum):
    AGENT = 'agent'
    TASK = 'task'
    TOOLS = 'tools'
    SPECIAL = 'special'


class Node(pydantic.BaseModel):
    name: str
    type: NodeType


class Edge(pydantic.BaseModel):
    source: Node
    target: Node
