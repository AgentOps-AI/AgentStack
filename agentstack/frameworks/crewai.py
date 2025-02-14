from typing import Optional, Any, Callable
from pathlib import Path
import ast
from agentstack import conf, log
from agentstack.exceptions import ValidationError
from agentstack.generation import InsertionPoint
from agentstack.frameworks import BaseEntrypointFile
from agentstack._tools import ToolConfig
from agentstack.tasks import TaskConfig
from agentstack.agents import AgentConfig
from agentstack.generation import asttools
from agentstack import graph


NAME: str = "CrewAI"
ENTRYPOINT: Path = Path('src/crew.py')


class CrewFile(BaseEntrypointFile):
    """
    Parses and manipulates the CrewAI entrypoint file.
    All AST interactions should happen within the methods of this class.
    """

    def write(self):
        """
        Early versions of the crew entrypoint file used tabs instead of spaces.
        This method replaces all tabs with 4 spaces before writing the file to
        avoid SyntaxErrors.
        """
        self.source = self.source.replace('\t', '    ')
        super().write()

    def get_base_class(self) -> ast.ClassDef:
        """A base class is a class decorated with `@CrewBase`."""
        try:
            return asttools.find_class_with_decorator(self.tree, 'CrewBase')[0]
        except IndexError:
            raise ValidationError(f"`@CrewBase` decorated class not found in {ENTRYPOINT}")

    def get_run_method(self) -> ast.FunctionDef:
        """A run method is a method decorated with `@crew`."""
        try:
            base_class = self.get_base_class()
            return asttools.find_decorated_method_in_class(base_class, 'crew')[0]
        except IndexError:
            raise ValidationError(
                f"`@crew` decorated method not found in `{base_class.name}` in {ENTRYPOINT}"
            )

    def get_new_task_method(self, task: TaskConfig) -> str:
        """Get the content of a new task method."""
        return f"""    @task
    def {task.name}(self) -> Task:
        return Task(
            config=self.tasks_config['{task.name}'],
        )"""

    def get_new_agent_method(self, agent: AgentConfig) -> str:
        """Get the content of a new agent method."""
        return f"""    @agent
    def {agent.name}(self) -> Agent:
        return Agent(
            config=self.agents_config['{agent.name}'],
            tools=[], # add tools here or use `agentstack tools add <tool_name>
            verbose=True,
        )"""

    def get_agent_tools(self, agent_name: str) -> ast.List:
        """
        Get the list of tools used by an agent as an AST List node.

        Tool definitions are inside of the methods marked with an `@agent` decorator.
        The method returns a new class instance with the tools as a list of callables
        under the kwarg `tools`.
        """
        method = asttools.find_method(self.get_agent_methods(), agent_name)
        if method is None:
            raise ValidationError(f"Method `{agent_name}` does not exist in {ENTRYPOINT}")

        agent_class = asttools.find_class_instantiation(method, 'Agent')
        if agent_class is None:
            raise ValidationError(f"Method `{agent_name}` does not call `Agent` in {ENTRYPOINT}")

        tools_kwarg = asttools.find_kwarg_in_method_call(agent_class, 'tools')
        if not tools_kwarg:
            raise ValidationError(f"`Agent` does not have a kwarg `tools` in {ENTRYPOINT}")

        if not isinstance(tools_kwarg.value, ast.List):
            raise ValidationError(f"`Agent` must define a list for kwarg `tools` in {ENTRYPOINT}")

        return tools_kwarg.value


def get_entrypoint() -> CrewFile:
    """
    Get the CrewAI entrypoint file.
    """
    return CrewFile(conf.PATH / ENTRYPOINT)


def validate_project() -> None:
    """
    Validate that a CrewAI project is ready to run.
    Raises an `agentstack.ValidationError` if the project is not valid.
    """
    return  # We don't need to do any additional validation


def add_task(task: TaskConfig, position: Optional[InsertionPoint] = None) -> None:
    """
    Add a task method to the CrewAI entrypoint.
    """
    if position is not None:
        raise NotImplementedError(f"Task insertion points are not supported in {NAME}.")

    with get_entrypoint() as entrypoint:
        entrypoint.add_task_method(task)


def add_agent(agent: AgentConfig, position: Optional[InsertionPoint] = None) -> None:
    """
    Add an agent method to the CrewAI entrypoint.
    """
    if position is not None:
        raise NotImplementedError(f"Agent insertion points are not supported in {NAME}.")

    with get_entrypoint() as entrypoint:
        entrypoint.add_agent_method(agent)


def add_tool(tool: ToolConfig, agent_name: str):
    """
    Add a tool to the CrewAI entrypoint for the specified agent.
    The agent should already exist in the crew class and have a keyword argument `tools`.
    """
    with get_entrypoint() as entrypoint:
        entrypoint.add_agent_tools(agent_name, tool)


def remove_tool(tool: ToolConfig, agent_name: str):
    """
    Remove a tool from the CrewAI framework for the specified agent.
    """
    with get_entrypoint() as entrypoint:
        entrypoint.remove_agent_tools(agent_name, tool)


def wrap_tool(tool_func: Callable) -> Callable:
    """
    Wrap a tool function with framework-specific functionality.
    """
    try:
        from crewai.tools import tool as _crewai_tool_decorator
    except ImportError:
        raise ValidationError(f"Could not import `crewai`. Is this an AgentStack {NAME} project?")

    return _crewai_tool_decorator(tool_func)


def get_graph() -> list[graph.Edge]:
    """Get the graph of the user's project."""
    log.debug(f"{NAME} does not support graph generation.")
    return []
