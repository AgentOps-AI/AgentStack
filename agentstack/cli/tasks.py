from typing import Optional
from agentstack import conf
from agentstack import repo
from agentstack.cli import parse_insertion_point
from agentstack import generation


def add_task(
    name: str,
    description: Optional[str] = None,
    expected_output: Optional[str] = None,
    agent: Optional[str] = None,
    position: Optional[str] = None,
):
    """
    Add a task to the user's project.
    """
    conf.assert_project()
    _position = parse_insertion_point(position)

    repo.commit_user_changes()
    with repo.Transaction() as commit:
        commit.add_message(f"Added task {name}")
        generation.add_task(
            name=name,
            description=description,
            expected_output=expected_output,
            agent=agent,
            position=_position,
        )
