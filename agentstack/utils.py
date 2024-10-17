from typing import Optional

import toml
import os
import sys
import json
import re


def get_version():
    try:
        with open('../pyproject.toml', 'r') as f:
            pyproject_data = toml.load(f)
            return pyproject_data['project']['version']
    except (KeyError, FileNotFoundError) as e:
        print(e)
        return "Unknown version"


def verify_agentstack_project():
    if not os.path.isfile('agentstack.json'):
        print("\033[31mAgentStack Error: This does not appear to be an AgentStack project."
              "\nPlease ensure you're at the root directory of your project and a file named agentstack.json exists. "
              "If you're starting a new project, run `agentstack init`\033[0m")
        sys.exit(1)


def get_framework(path: Optional[str] = None) -> str:
    try:
        file_path = 'agentstack.json'
        if path is not None:
            file_path = path + '/' + file_path

        agentstack_data = open_json_file(file_path)
        framework = agentstack_data.get('framework')

        if framework.lower() not in ['crewai', 'autogen', 'litellm']:
            print(term_color("agentstack.json contains an invalid framework", "red"))

        return framework
    except FileNotFoundError:
        print("\033[31mFile agentstack.json does not exist. Are you in the right directory?\033[0m")
        sys.exit(1)


def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_to_camel(s):
    return ''.join(word.title() for word in s.split('_'))


def open_json_file(path) -> dict:
    with open(path, 'r') as f:
        data = json.load(f)
    return data


def clean_input(input_string):
    special_char_pattern = re.compile(r'[^a-zA-Z0-9\s_]')
    return re.sub(special_char_pattern, '', input_string).lower().replace(' ', '_').replace('-', '_')


def term_color(text: str, color: str) -> str:
    if color is 'red':
        return "\033[91m{}\033[00m".format(text)
    if color is 'green':
        return "\033[92m{}\033[00m".format(text)
    else:
        return text
