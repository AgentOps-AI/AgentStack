import sys
from typing import Optional
from agentstack import log
from agentstack.exceptions import ValidationError
from agentstack.conf import ConfigFile
from agentstack import frameworks
from agentstack.utils import verify_agentstack_project
from agentstack.agents import AgentConfig, AGENTS_FILENAME


def add_agent(
    agent_name: str,
    role: Optional[str] = None,
    goal: Optional[str] = None,
    backstory: Optional[str] = None,
    llm: Optional[str] = None,
):
    agentstack_config = ConfigFile()
    verify_agentstack_project()

    agent = AgentConfig(agent_name)
    with agent as config:
        config.role = role or "Add your role here"
        config.goal = goal or "Add your goal here"
        config.backstory = backstory or "Add your backstory here"
        config.llm = llm or agentstack_config.default_model or ""

    try:
        frameworks.add_agent(agent)
        log.info(f"Added agent \"{agent_name}\" to project.")
    except ValidationError as e:
        raise ValidationError(f"Error adding agent to project:\n{e}")

    log.success(f"Added agent \"{agent_name}\" to your AgentStack project successfully!")
