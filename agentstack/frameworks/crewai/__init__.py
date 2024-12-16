"""CrewAI framework implementation."""

from typing import Any, Dict, List, Optional, Set
from pathlib import Path
from agentstack.tools import ToolConfig
from agentstack.tasks import TaskConfig
from agentstack.agents import AgentConfig
from agentstack.exceptions import ValidationError

ENTRYPOINT = "src/main.py"

_framework_instance = None

def get_framework():
    """Get or create the framework instance."""
    global _framework_instance
    if _framework_instance is None:
        _framework_instance = CrewAIFramework()
    return _framework_instance

def add_tool(tool_name: str, tool: ToolConfig) -> None:
    """Add a tool to the framework."""
    framework = get_framework()
    framework.add_tool(tool_name, tool)

def add_agent(agent: AgentConfig) -> None:
    """Add an agent to the framework."""
    framework = get_framework()
    framework.add_agent(agent)

def get_agent_names() -> List[str]:
    """Get a list of agent names."""
    framework = get_framework()
    return list(framework.agents.keys())

def validate_project() -> bool:
    """Validate that the project structure is correct."""
    if not Path(ENTRYPOINT).exists():
        raise ValidationError(f"Project validation failed: {ENTRYPOINT} does not exist")
    return True

class CrewAIFramework:
    """Framework implementation for CrewAI."""

    def __init__(self) -> None:
        """Initialize the CrewAI framework."""
        self.tools: Dict[str, ToolConfig] = {}
        self.tasks: Dict[str, TaskConfig] = {}
        self.agents: Dict[str, AgentConfig] = {}
        self._tool_names: Set[str] = set()

    def add_tool(self, tool_name: str, tool: ToolConfig) -> None:
        """Add a tool to the framework."""
        self.tools[tool_name] = tool
        self._tool_names.add(tool_name)

    def get_tool(self, tool_name: str) -> Optional[ToolConfig]:
        """Get a tool by name."""
        return self.tools.get(tool_name)

    def add_task(self, task: TaskConfig) -> None:
        """Add a task to the framework."""
        self.tasks[task.name] = task

    def add_agent(self, agent: AgentConfig) -> None:
        """Add an agent to the framework."""
        self.agents[agent.name] = agent
