import toml
import os
import sys
import json

from ruamel.yaml.scalarstring import FoldedScalarString


def get_version():
    try:
        with open('pyproject.toml', 'r') as f:
            pyproject_data = toml.load(f)
            return pyproject_data['tool']['poetry']['version']
    except (KeyError, FileNotFoundError):
        return "Unknown version"


def verify_agentstack_project():
    if not os.path.isfile('agentstack.json'):
        print("\033[31mAgentStack Error: This does not appear to be an AgentStack project."
              "\nPlease ensure you're at the root directory of your project and a file named agentstack.json exists. "
              "If you're starting a new project, run `agentstack init`\033[0m")
        sys.exit(1)


def get_framework() -> str:
    try:
        with open('agentstack.json', 'r') as f:
            data = json.load(f)
            framework = data.get('framework')

            if framework.lower() not in ['crewai', 'autogen', 'litellm']:
                print("\033[31magentstack.json contains an invalid framework\033[0m")

            return framework
    except FileNotFoundError:
        print("\033[31mFile agentstack.json does not exist.\033[0m")
        sys.exit(1)
