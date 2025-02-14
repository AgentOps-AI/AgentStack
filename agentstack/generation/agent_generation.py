import sys
from typing import TYPE_CHECKING, Optional
from agentstack import log
from agentstack.exceptions import ValidationError
from agentstack.conf import ConfigFile
from agentstack import frameworks
from agentstack.utils import verify_agentstack_project
from agentstack.agents import AgentConfig, AGENTS_FILENAME

if TYPE_CHECKING:
    from agentstack.generation import InsertionPoint


def add_agent(
    name: str,
    role: Optional[str] = None,
    goal: Optional[str] = None,
    backstory: Optional[str] = None,
    llm: Optional[str] = None,
    allow_delegation: Optional[bool] = None,
    position: Optional['InsertionPoint'] = None,
):
    agentstack_config = ConfigFile()
    verify_agentstack_project()

    agent = AgentConfig(name)
    with agent as config:
        config.role = role or "Add your role here"
        config.goal = goal or "Add your goal here"
        config.backstory = backstory or "Add your backstory here"
        config.llm = llm or agentstack_config.default_model or ""

        if allow_delegation:
            log.warning("Agent allow_delegation is not implemented.")

    try:
        frameworks.add_agent(agent, position)
    except ValidationError as e:
        raise ValidationError(f"Error adding agent to project:\n{e}")

    log.success(f"🤖 Added agent \"{agent.name}\" to your AgentStack project successfully!")
