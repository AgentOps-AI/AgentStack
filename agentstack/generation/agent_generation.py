from typing import Optional

from .gen_utils import insert_code_after_tag
from agentstack.utils import verify_agentstack_project, get_framework
import os
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import FoldedScalarString


def generate_agent(
        name,
        role: Optional[str],
        goal: Optional[str],
        backstory: Optional[str],
        llm: Optional[str]
):
    if not role:
        role = 'Add your role here'
    if not goal:
        goal = 'Add your goal here'
    if not backstory:
        backstory = 'Add your backstory here'
    if not llm:
        llm = 'Add your llm here with format provider/model'

    verify_agentstack_project()

    framework = get_framework()

    if framework == 'crewai':
        generate_crew_agent(name, role, goal, backstory, llm)
        print("    > Added to src/config/agents.yaml")
    else:
        print(f"This function is not yet implemented for {framework}")
        return

    print(f"Added agent \"{name}\" to your AgentStack project successfully!")





def generate_crew_agent(
        name,
        role: Optional[str] = 'Add your role here',
        goal: Optional[str] = 'Add your goal here',
        backstory: Optional[str] = 'Add your backstory here',
        llm: Optional[str] = 'Add your llm here with format provider/model'
):
    config_path = os.path.join('src', 'config', 'agents.yaml')

    # Ensure the directory exists
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    yaml = YAML()
    yaml.preserve_quotes = True  # Preserve quotes in existing data

    # Read existing data
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            try:
                data = yaml.load(file) or {}
            except Exception as exc:
                print(f"Error parsing YAML file: {exc}")
                data = {}
    else:
        data = {}

    # Handle None values
    role_str = FoldedScalarString(role) if role else FoldedScalarString('')
    goals_str = FoldedScalarString(goal) if goal else FoldedScalarString('')
    backstory_str = FoldedScalarString(backstory) if backstory else FoldedScalarString('')
    model_str = llm if llm else ''

    # Add new agent details
    data[name] = {
        'role': role_str,
        'goal': goals_str,
        'backstory': backstory_str,
        'llm': model_str
    }

    # Write back to the file without altering existing content
    with open(config_path, 'w') as file:
        yaml.dump(data, file)

    # Now lets add the agent to crew.py
    file_path = 'src/crew.py'
    tag = '# Agent definitions'
    code_to_insert = [
        "@agent",
        f"def {name}(self) -> Agent:",
        "    return Agent(",
        f"        config=self.agents_config['{name}'],",
        "        tools=[],  # add tools here or use `agentstack tools add <tool_name>",  # TODO: Add any tools in agentstack.json
        "        verbose=True",
        "    )",
        ""
    ]

    insert_code_after_tag(file_path, tag, code_to_insert)
