from typing import Optional
from pathlib import Path
from agentstack.exceptions import ValidationError
from agentstack.tools import ToolConfig
from agentstack.agents import AgentConfig
from agentstack.tasks import TaskConfig

ENTRYPOINT: Path = Path('src/graph.py')  # Adjust this path as needed for langgraph


def validate_project() -> None:
    """
    Validate that a langgraph project is ready to run.
    Raises an `agentstack.ValidationError` if the project is not valid.
    """
    # Implementation here
    pass

def get_tool_names() -> list[str]:
    """
    Get a list of tool names in the user's project.
    """
    # Implementation here
    pass

def add_tool(tool: ToolConfig, agent_name: str) -> None:
    """
    Add a tool to an agent in the user's project.
    """
    # Implementation here
    pass

def remove_tool(tool: ToolConfig, agent_name: str) -> None:
    """
    Remove a tool from an agent in user's project.
    """
    # Implementation here
    pass

def get_agent_names() -> list[str]:
    """
    Get a list of agent names in the user's project.
    """
    # Implementation here
    pass

def get_agent_tool_names(agent_name: str) -> list[str]:
    """
    Get a list of tool names in an agent in the user's project.
    """
    # Implementation here
    pass

def add_agent(agent: AgentConfig) -> None:
    """
    Add an agent to the user's project.
    """
    # Implementation here
    pass

def add_task(task: TaskConfig) -> None:
    """
    Add a task to the user's project.
    """
    # Implementation here
    pass

def get_task_names() -> list[str]:
    """
    Get a list of task names in the user's project.
    """
    # Implementation here
    pass
