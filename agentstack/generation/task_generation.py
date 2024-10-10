from typing import Optional

from .gen_utils import insert_code_after_tag
from ..utils import verify_agentstack_project, get_framework
import os
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import FoldedScalarString


def generate_task(
        name,
        description: Optional[str],
        expected_output: Optional[str],
        agent: Optional[str]
):
    if not description:
        description = 'Add your description here'
    if not expected_output:
        expected_output = 'Add your expected_output here'
    if not agent:
        agent = 'default_agent'

    verify_agentstack_project()

    framework = get_framework()

    if framework == 'crewai':
        generate_crew_task(name, description, expected_output, agent)
        print("    > Added to src/config/tasks.yaml")
    else:
        print(f"This function is not yet implemented for {framework}")
        return

    print(f"Added task \"{name}\" to your AgentStack project successfully!")


def generate_crew_task(
        name,
        description: Optional[str],
        expected_output: Optional[str],
        agent: Optional[str]
):
    config_path = os.path.join('src', 'config', 'tasks.yaml')

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
    description_str = FoldedScalarString(description) if description else FoldedScalarString('')
    expected_output_str = FoldedScalarString(expected_output) if expected_output else FoldedScalarString('')
    agent_str = FoldedScalarString(agent) if agent else FoldedScalarString('')

    # Add new agent details
    data[name] = {
        'description': description_str,
        'expected_output': expected_output_str,
        'agent': agent_str,
    }

    # Write back to the file without altering existing content
    with open(config_path, 'w') as file:
        yaml.dump(data, file)

    # Add task to crew.py
    file_path = 'src/crew.py'
    tag = '# Task definitions'
    code_to_insert = [
        "@task",
        f"def {name}(self) -> Task:",
        "    return Task(",
        f"        config=self.tasks_config['{name}'],",
        "    )",
        ""
    ]

    insert_code_after_tag(file_path, tag, code_to_insert)
