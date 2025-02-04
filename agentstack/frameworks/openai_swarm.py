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


NAME: str = "OpenAI Swarm"
ENTRYPOINT: Path = Path('src/stack.py')


class SwarmFile(BaseEntrypointFile):
    """
    Parses and manipulates the entrypoint file.
    All AST interactions should happen within the methods of this class.
    """

    def get_new_task_method(self, task: TaskConfig) -> str:
        """Get the content of a new task method."""
        return f"""    @agentstack.task
    def {task.name}(self, messages: list[str] = []) -> Agent:
        task_config = agentstack.get_task('{task.name}')
        agent = getattr(self, task_config.agent)
        messages = [
            *messages, 
            task_config.prompt, 
        ]
        return agent(messages)"""

    def get_new_agent_method(self, agent: AgentConfig) -> str:
        """Get the content of a new agent method."""
        return f"""    @agentstack.agent
    def {agent.name}(self, messages: list[str] = []) -> Agent:
        agent_config = agentstack.get_agent('{agent.name}')
        messages = [
            agent_config.prompt,
            *messages,
        ]
        return Agent(
            name=agent_config.name, 
            model=agent_config.model, 
            instructions='\\n'.join(messages),
            functions=[],
        )"""

    def get_agent_tools(self, agent_name: str) -> ast.List:
        """Get the list of tools used by an agent as an AST List node."""
        method = asttools.find_method(self.get_agent_methods(), agent_name)
        if method is None:
            raise ValidationError(f"Agent method `{agent_name}` does not exist in {ENTRYPOINT}")

        # find the `functions` keyword argument to `Agent` inside method
        try:
            agent_init = asttools.find_method_calls(method, 'Agent')[0]
        except IndexError:
            raise ValidationError(f"Agent method `{agent_name}` does not instantiate `Agent` in {ENTRYPOINT}")

        tools_kwarg = asttools.find_kwarg_in_method_call(agent_init, 'functions')

        if not tools_kwarg:
            raise ValidationError(f"`Agent` does not have a keyword argument `functions` in {ENTRYPOINT}")

        if not isinstance(tools_kwarg.value, ast.List):
            raise ValidationError(f"`Agent` must define a list for kwarg `tools` in {ENTRYPOINT}")

        return tools_kwarg.value


def get_entrypoint() -> SwarmFile:
    """
    Get the entrypoint file.
    """
    return SwarmFile(conf.PATH / ENTRYPOINT)


def validate_project() -> None:
    """
    Validate that the project is ready to run.
    Raises an `agentstack.ValidationError` if the project is not valid.
    """
    return  # No additional validation needed


def add_task(task: TaskConfig, position: Optional[InsertionPoint] = None) -> None:
    """
    Add a task method to the entrypoint.
    """
    if position is not None:
        raise NotImplementedError(f"Task insertion points are not supported in {NAME}.")

    with get_entrypoint() as entrypoint:
        entrypoint.add_task_method(task)


def add_agent(agent: AgentConfig, position: Optional[InsertionPoint] = None) -> None:
    """
    Add an agent method to the entrypoint.
    """
    if position is not None:
        raise NotImplementedError(f"Agent insertion points are not supported in {NAME}.")

    with get_entrypoint() as entrypoint:
        entrypoint.add_agent_method(agent)


def add_tool(tool: ToolConfig, agent_name: str):
    """
    Add a tool to the entrypoint for the specified agent.
    """
    with get_entrypoint() as entrypoint:
        entrypoint.add_agent_tools(agent_name, tool)


def remove_tool(tool: ToolConfig, agent_name: str):
    """
    Remove a tool from the entrypoint for the specified agent.
    """
    with get_entrypoint() as entrypoint:
        entrypoint.remove_agent_tools(agent_name, tool)


def wrap_tool(tool_func: Callable) -> Callable:
    """
    Wrap a tool function with framework-specific functionality.
    """
    # Swarm agents accept raw functions as tools, so no wrapping is needed.
    return tool_func


def get_graph() -> list[graph.Edge]:
    """Get the graph of the user's project."""
    log.debug(f"{NAME} does not support graph generation.")
    return []
