import sys
from typing import Optional
from pathlib import Path
from agentstack import ValidationError
from agentstack import frameworks
from agentstack.utils import verify_agentstack_project
from agentstack.agents import AgentConfig, AGENTS_FILENAME
from agentstack.generation.files import ConfigFile


def add_agent(
        agent_name: str, 
        role: Optional[str] = None, 
        goal: Optional[str] = None, 
        backstory: Optional[str] = None, 
        llm: Optional[str] = None, 
        path: Optional[Path] = None):

    if path is None: path = Path()
    verify_agentstack_project(path)
    agentstack_config = ConfigFile(path)
    framework = agentstack_config.framework

    agent = AgentConfig(agent_name, path)
    with agent as config:
        config.role = role or "Add your role here"
        config.goal = goal or "Add your goal here"
        config.backstory = backstory or "Add your backstory here"
        config.llm = llm or agentstack_config.default_model
    
    try:
        frameworks.add_agent(framework, agent, path)
        print(f"    > Added to {AGENTS_FILENAME}")
    except ValidationError as e:
        print(f"Error adding agent to project:\n{e}")
        sys.exit(1)
    
    print(f"Added agent \"{agent_name}\" to your AgentStack project successfully!")

