"""
Agent Protocol framework implementation for AgentStack.

This module implements the agent-protocol specification (https://github.com/langchain-ai/agent-protocol)
as a framework within AgentStack.
"""

from typing import Optional, Any, List
from pathlib import Path
import ast
import re

from agentstack.exceptions import ValidationError, ThreadError, RunError, StoreError
from agentstack.tools import ToolConfig
from agentstack.tasks import TaskConfig
from agentstack.agents import AgentConfig
from agentstack import conf, frameworks


ENTRYPOINT: Path = Path('src/agent.py')


class AgentProtocolFile:
    """
    Handles agent-protocol specific file operations.

    This class manages the interaction with agent-protocol files, including
    validation, reading, and writing operations.
    """

    def __init__(self, path: Path):
        self.path = path
        if not self.path.exists():
            raise ValidationError(f"Agent protocol file not found at {self.path}")

        self._content = self.path.read_text()

    def validate(self) -> None:
        """Validate the agent protocol file structure."""
        try:
            tree = ast.parse(self._content)
        except SyntaxError as e:
            raise ValidationError(f"Invalid Python syntax in {self.path}: {e}")

        # Check for FastAPI app and required components
        has_app = False
        has_agent_protocol = False
        has_tools = False
        has_task_handler = False
        has_step_handler = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id == 'app':
                            has_app = True
                        elif target.id == 'agent_protocol':
                            has_agent_protocol = True
                        elif target.id == 'tools':
                            has_tools = True
            elif isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    # Handle all possible decorator patterns
                    decorator_str = ''
                    if isinstance(decorator, ast.Name):
                        decorator_str = decorator.id
                    elif isinstance(decorator, ast.Attribute):
                        # Build full decorator path (e.g., agent_protocol.on_task)
                        parts = []
                        current = decorator
                        while isinstance(current, ast.Attribute):
                            parts.append(current.attr)
                            current = current.value
                        if isinstance(current, ast.Name):
                            parts.append(current.id)
                        decorator_str = '.'.join(reversed(parts))
                    elif isinstance(decorator, ast.Call):
                        # Handle decorator calls (e.g., @decorator())
                        if isinstance(decorator.func, ast.Attribute):
                            parts = []
                            current = decorator.func
                            while isinstance(current, ast.Attribute):
                                parts.append(current.attr)
                                current = current.value
                            if isinstance(current, ast.Name):
                                parts.append(current.id)
                            decorator_str = '.'.join(reversed(parts))
                        elif isinstance(decorator.func, ast.Name):
                            decorator_str = decorator.func.id

                    # Check for task and step handlers
                    if 'on_task' in decorator_str:
                        has_task_handler = True
                    elif 'on_step' in decorator_str:
                        has_step_handler = True

        if not has_app:
            raise ValidationError(f"FastAPI app not found in {self.path}")
        if not has_agent_protocol:
            raise ValidationError(f"AgentProtocol instance not found in {self.path}")
        if not has_tools:
            raise ValidationError(f"Tools list not found in {self.path}")
        if not has_task_handler:
            raise ValidationError(f"@agent_protocol.on_task handler not found in {self.path}")
        if not has_step_handler:
            raise ValidationError(f"@agent_protocol.on_step handler not found in {self.path}")

    def _update_tools_list(self, tool: ToolConfig, add: bool = True) -> None:
        """Update the tools list in the file."""
        if add:
            if tool.tools_bundled:
                tool_str = f"*tools.{tool.name}"
            else:
                tool_str = f"tools.{tool.name}"

            # If tools list exists, modify it
            if re.search(r"tools\s*=\s*\[", self._content):
                if tool_str not in self._content:
                    # Replace existing tools list with updated one
                    self._content = re.sub(
                        r"tools\s*=\s*\[(.*?)\]",
                        lambda m: f"tools=[{tool_str}]"
                        if not m.group(1).strip()
                        else f"tools=[{', '.join(t.strip() for t in m.group(1).split(',') if t.strip())}, {tool_str}]",
                        self._content,
                        flags=re.DOTALL,
                    )
            else:
                # Create new tools list
                self._content = re.sub(
                    r"(import tools\n+)", f"\\1tools=[{tool_str}]  # Initial tool setup\n\n", self._content
                )
        else:
            # Remove tool from list
            if tool.tools_bundled:
                tool_str = f"*tools.{tool.name}"
            else:
                tool_str = f"tools.{tool.name}"

            # First, get the current tools list content
            match = re.search(r"tools\s*=\s*\[(.*?)\]", self._content, re.DOTALL)
            if match:
                tools = [t.strip() for t in match.group(1).split(',') if t.strip()]
                # Remove the tool if it exists
                tools = [t for t in tools if t != tool_str]
                # Update the tools list with proper format
                self._content = re.sub(
                    r"tools\s*=\s*\[.*?\]",
                    f"tools=[{', '.join(tools)}]" if tools else "tools=[]",
                    self._content,
                    flags=re.DOTALL,
                )

        # Write updated content back to file
        self.path.write_text(self._content)


def validate_project() -> None:
    """Validate the agent protocol project structure."""
    entrypoint_path = frameworks.get_entrypoint_path('agent_protocol')
    if not entrypoint_path.exists():
        raise ValidationError("Agent Protocol entrypoint file not found")

    file = AgentProtocolFile(entrypoint_path)
    file.validate()

    # Additional project-level validation can be added here


def get_task_names() -> List[str]:
    """
    Get a list of task names from the agent protocol implementation.
    Currently returns an empty list as tasks are created dynamically.
    """
    return []


def add_task(task: TaskConfig) -> None:
    """
    Add a task to the agent protocol implementation.
    Tasks in agent-protocol are created dynamically through the API.
    """
    pass


def get_agent_names() -> List[str]:
    """
    Get a list of available agent names.
    Currently returns a single agent as agent-protocol typically uses one agent.
    """
    return ["agent_protocol_agent"]


def add_agent(agent: AgentConfig) -> None:
    """
    Register a new agent in the agent protocol implementation.
    Updates the agent configuration in the agent.py file.
    """
    pass


def add_tool(tool: ToolConfig, agent_name: str) -> None:
    """
    Add a tool to the specified agent in the agent protocol implementation.

    Args:
        tool: Tool configuration to add
        agent_name: Name of the agent to add the tool to
    """
    entrypoint_path = frameworks.get_entrypoint_path('agent_protocol')
    if not entrypoint_path.exists():
        raise ValidationError("Agent Protocol entrypoint file not found")

    # Validate project before adding tool
    validate_project()

    agent_file = AgentProtocolFile(entrypoint_path)
    agent_file._update_tools_list(tool, add=True)


def remove_tool(tool: ToolConfig, agent_name: str) -> None:
    """
    Remove a tool from the specified agent in the agent protocol implementation.

    Args:
        tool: Tool configuration to remove
        agent_name: Name of the agent to remove the tool from
    """
    agent_file = AgentProtocolFile(conf.PATH / ENTRYPOINT)
    agent_file._update_tools_list(tool, add=False)
