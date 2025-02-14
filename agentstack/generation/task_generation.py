from typing import TYPE_CHECKING, Optional
from pathlib import Path
from agentstack import log
from agentstack.exceptions import ValidationError
from agentstack import frameworks
from agentstack.utils import verify_agentstack_project
from agentstack.tasks import TaskConfig, TASKS_FILENAME

if TYPE_CHECKING:
    from agentstack.generation import InsertionPoint


def add_task(
    name: str,
    description: Optional[str] = None,
    expected_output: Optional[str] = None,
    agent: Optional[str] = None,
    position: Optional['InsertionPoint'] = None,
):
    verify_agentstack_project()

    agents = frameworks.get_agent_method_names()
    if not agent and len(agents) == 1:
        # if there's only one agent, use it by default
        agent = agents[0]

    task = TaskConfig(name)
    with task as config:
        config.description = description or "Add your description here"
        config.expected_output = expected_output or "Add your expected_output here"
        config.agent = agent or "agent_name"

    try:
        frameworks.add_task(task, position)
    except ValidationError as e:
        raise ValidationError(f"Error adding task to project:\n{e}")

    log.success(f"📃 Added task \"{task.name}\" to your AgentStack project successfully!")

