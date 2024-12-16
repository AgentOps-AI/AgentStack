"""CrewAI framework implementation."""

from typing import Any, Dict, List, Optional, Set
from pathlib import Path
import ast
import shutil
from agentstack.tools import ToolConfig
from agentstack.tasks import TaskConfig
from agentstack.agents import AgentConfig
from agentstack.exceptions import ValidationError
from agentstack.generation import asttools
from agentstack.conf import get_path

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

def remove_tool(tool: ToolConfig, agent_name: str) -> None:
    """Remove a tool from the framework."""
    framework = get_framework()
    framework.remove_tool(tool, agent_name)

def add_agent(agent: AgentConfig) -> None:
    """Add an agent to the framework."""
    framework = get_framework()
    framework.add_agent(agent)

def add_task(task: TaskConfig) -> None:
    """Add a task to the framework."""
    framework = get_framework()
    framework.add_task(task)

def get_agent_names() -> List[str]:
    """Get a list of agent names."""
    framework = get_framework()
    return list(framework.agents.keys())

def validate_project() -> bool:
    """Validate that the project structure is correct."""
    try:
        project_dir = Path("src")
        if not project_dir.exists():
            raise ValidationError("Project directory 'src' does not exist")
        main_file = project_dir / "main.py"
        if not main_file.exists():
            raise ValidationError("Main file 'src/main.py' does not exist")
        return True
    except Exception as e:
        raise ValidationError(f"Project validation failed: {str(e)}")

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
        self._update_agent_tools(tool, add=True)

    def remove_tool(self, tool: ToolConfig, agent_name: str) -> None:
        """Remove a tool from the framework."""
        if tool.name in self.tools:
            self._update_agent_tools(tool, add=False)
            del self.tools[tool.name]
            self._tool_names.remove(tool.name)

    def _update_agent_tools(self, tool: ToolConfig, add: bool = True) -> None:
        """Update agent tools in the entrypoint file."""
        try:
            project_path = get_path()
            entrypoint_path = project_path / ENTRYPOINT
            if not entrypoint_path.exists():
                entrypoint_path.parent.mkdir(parents=True, exist_ok=True)
                fixtures_path = Path(__file__).parent.parent.parent.parent / 'tests' / 'fixtures'
                template_path = fixtures_path / 'frameworks' / get_framework() / 'entrypoint_min.py'
                if template_path.exists():
                    shutil.copy(template_path, entrypoint_path)
                else:
                    entrypoint_path.touch()

            with open(entrypoint_path, 'r') as f:
                tree = ast.parse(f.read())

            # Find the agent method
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and hasattr(node, 'decorator_list'):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Name) and decorator.id == 'agent':
                            # Find the Agent constructor call
                            for child in ast.walk(node):
                                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == 'Agent':
                                    # Find or create the tools argument
                                    tools_keyword = None
                                    for keyword in child.keywords:
                                        if keyword.arg == 'tools':
                                            tools_keyword = keyword
                                            break

                                    if not tools_keyword:
                                        tools_keyword = ast.keyword(
                                            arg='tools',
                                            value=ast.List(elts=[], ctx=ast.Load())
                                        )
                                        child.keywords.append(tools_keyword)

                                    if add:
                                        # Add the tool to the list
                                        tool_ref = f"tools.{tool.name}" if not tool.tools_bundled else f"*tools.{tool.name}"
                                        tool_node = ast.parse(tool_ref).body[0]
                                        if isinstance(tool_node, ast.Expr):
                                            tool_expr = tool_node.value
                                            if not any(ast.unparse(elem) == ast.unparse(tool_expr) for elem in tools_keyword.value.elts):
                                                tools_keyword.value.elts.append(tool_expr)
                                    else:
                                        # Remove the tool from the list
                                        tool_ref = f"tools.{tool.name}" if not tool.tools_bundled else f"*tools.{tool.name}"
                                        tools_keyword.value.elts = [
                                            elem for elem in tools_keyword.value.elts
                                            if ast.unparse(elem) != tool_ref
                                        ]

            # Write back the modified file
            with open(entrypoint_path, 'w') as f:
                f.write(ast.unparse(tree))

        except Exception as e:
            raise ValidationError(f"Failed to update agent tools: {str(e)}")

    def get_tool(self, tool_name: str) -> Optional[ToolConfig]:
        """Get a tool by name."""
        return self.tools.get(tool_name)

    def add_task(self, task: TaskConfig) -> None:
        """Add a task to the framework."""
        self.tasks[task.name] = task

    def add_agent(self, agent: AgentConfig) -> None:
        """Add an agent to the framework."""
        self.agents[agent.name] = agent
