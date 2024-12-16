"""CrewAI framework implementation."""

from typing import Any, Dict, List, Optional
from agentstack.tools import ToolConfig
from agentstack.tasks import TaskConfig
from agentstack.agents import AgentConfig


class CrewAIFramework:
    """Framework implementation for CrewAI."""

    def __init__(self) -> None:
        """Initialize the CrewAI framework."""
        self.tools: Dict[str, Any] = {}
        self.tasks: Dict[str, TaskConfig] = {}
        self.agents: Dict[str, AgentConfig] = {}

    def add_tool(self, tool: ToolConfig) -> None:
        """Add a tool to the framework."""
        for tool_name in tool.tools:
            self.tools[tool_name] = tool

    def get_tool(self, tool_name: str) -> Optional[ToolConfig]:
        """Get a tool by name."""
        return self.tools.get(tool_name)

    def add_task(self, task: TaskConfig) -> None:
        """Add a task to the framework."""
        self.tasks[task.name] = task

    def add_agent(self, agent: AgentConfig) -> None:
        """Add an agent to the framework."""
        self.agents[agent.name] = agent
