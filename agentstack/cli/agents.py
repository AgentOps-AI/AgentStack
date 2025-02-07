from typing import Optional
from agentstack import conf
from agentstack import repo
from agentstack.cli import configure_default_model, parse_insertion_point
from agentstack import generation


def add_agent(
    name: str,
    role: Optional[str] = None,
    goal: Optional[str] = None,
    backstory: Optional[str] = None,
    llm: Optional[str] = None,
    position: Optional[str] = None,
):
    """
    Add an agent to the user's project.
    """
    conf.assert_project()
    if not llm:
        configure_default_model()
    _position = parse_insertion_point(position)

    repo.commit_user_changes()
    with repo.Transaction() as commit:
        commit.add_message(f"Added agent {name}")
        generation.add_agent(
            name=name,
            role=role,
            goal=goal,
            backstory=backstory,
            llm=llm,
            position=_position,
        )
