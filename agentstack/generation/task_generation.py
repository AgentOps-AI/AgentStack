import sys
from typing import Optional
from pathlib import Path
from agentstack.exceptions import ValidationError
from agentstack import frameworks
from agentstack.utils import verify_agentstack_project
from agentstack.tasks import TaskConfig, TASKS_FILENAME


def add_task(
    task_name: str,
    description: Optional[str] = None,
    expected_output: Optional[str] = None,
    agent: Optional[str] = None,
):
    verify_agentstack_project()

    task = TaskConfig(task_name)
    with task as config:
        config.description = description or "Add your description here"
        config.expected_output = expected_output or "Add your expected_output here"
        config.agent = agent or "agent_name"

    try:
        frameworks.add_task(task)
        print(f"    > Added to {TASKS_FILENAME}")
    except ValidationError as e:
        print(f"Error adding task to project:\n{e}")
        sys.exit(1)
    print(f"Added task \"{task_name}\" to your AgentStack project successfully!")
