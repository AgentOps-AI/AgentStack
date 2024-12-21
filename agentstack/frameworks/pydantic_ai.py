from typing import Optional, Callable
from pathlib import Path
from agentstack import conf
from agentstack.exceptions import ValidationError
from agentstack.tools import ToolConfig
from agentstack.tasks import TaskConfig
from agentstack.agents import AgentConfig
from agentstack.inputs import get_inputs
from agentstack.generation import asttools

try:
    import pydantic_ai  # unused, but maybe it's nice to validate now?
except ImportError as e:
    raise ValidationError(
        "Could not import `pydantic_ai`. "
        "Ensure you have installed the Pydantic AI version of AgentStack with: "
        "`uv pip install agentstack[pydantic_ai]`"
    ) from e

ENTRYPOINT: Path = Path("src/app.py")

PROMPT_AGENT: str = "You are {role}. {backstory}\nYour personal goal is: {goal}"
PROMPT_TASK: str = (
    "\nThis is the expect criteria for your final answer: {expected_output}\n "
    "you MUST return the actual complete content as the final answer, not a summary. "
    "\nCurrent Task: {description}\n\nBegin! This is VERY important to you, use the "
    "tools available and give your best Final Answer, your job depends on it!\n\nThought:"
)


class PydanticAIFile(asttools.File):
    pass


def _format_llm(llm: str) -> str:
    """
    Format the language model for Pydantic AI from the AgentStack format.
    "provider/model" -> "provider:model"
    """
    # TODO verify this is true with multiple slashes in the model name, too
    return llm.replace('/', ':')


def _format_system_prompt_for_agent(agent_config: AgentConfig) -> str:
    """
    Format the system prompt for an agent.
    """
    inputs = get_inputs()
    return PROMPT_AGENT.format(
        role=agent_config.role.format(**inputs),
        goal=agent_config.goal.format(**inputs),
        backstory=agent_config.backstory.format(**inputs),
    )


def _format_user_prompt_for_task(task_config: TaskConfig) -> str:
    """
    Format the user prompt for a task.
    """
    inputs = get_inputs()
    return PROMPT_TASK.format(
        description=task_config.description.format(**inputs),
        expected_output=task_config.expected_output.format(**inputs),
    )


def validate_project() -> None:
    """
    Validate that a user's project is ready to run.
    Raises a `ValidationError` if the project is not valid.
    """
    pass


def get_task_names() -> list[str]:
    """
    Get a list of task names in the user's project.
    """
    pass


def get_task_decorator_kwargs(task_name: str) -> dict:
    """
    Get the keyword arguments for the function affected by the agent decorator.
    """
    task_config = TaskConfig(task_name)
    inputs = get_inputs()
    return {
        'user_prompt': _format_user_prompt_for_task(task_config),
    }


def add_task(task: TaskConfig) -> None:
    """
    Add a task to the user's project.
    """
    pass


def get_agent_names() -> list[str]:
    """
    Get a list of agent names in the user's project.
    """
    pass


def get_agent_tool_names(agent_name: str) -> list[str]:
    """
    Get a list of tool names for an agent in the user's project.
    """
    pass


def get_agent_decorator_kwargs(agent_name: str) -> dict:
    """
    Get the keyword arguments for the function affected by the agent decorator.
    """
    agent_config = AgentConfig(agent_name)
    return {
        'name': agent_name,
        'model': _format_llm(agent_config.llm),
        'system_prompt': _format_system_prompt_for_agent(agent_config),
        'retries': agent_config.retries,
    }


def add_agent(agent: AgentConfig) -> None:
    """
    Add an agent to the user's project.
    """
    pass


def add_tool(tool: ToolConfig, agent_name: str) -> None:
    """
    Add a tool to an agent in the user's project.
    """
    pass


def remove_tool(tool: ToolConfig, agent_name: str) -> None:
    """
    Remove a tool from an agent in the user's project.
    """
    pass


def get_tool_callables(tool_name: str) -> list[Callable]:
    """
    Get a tool's implementations for use by a Pydantic AI agent.
    """
    # Pydantic AI wraps functional tools passed to the Agent `tools` attribute
    # automatically, so we don't need to do anything to prepare the tool for use.
    tool_config = ToolConfig.from_tool_name(tool_name)
    return tool_config.get_all_callables()
