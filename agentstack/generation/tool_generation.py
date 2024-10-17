import json
import sys
from typing import Optional

from .gen_utils import insert_code_after_tag
from ..utils import open_json_file, get_framework, term_color
import os
import shutil
import fileinput


def add_tool(tool_name: str, path: Optional[str] = None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tools = open_json_file(os.path.join(script_dir, '..', 'tools', 'tools.json'))
    framework = get_framework(path)
    assert_tool_exists(tool_name, tools)

    tool_data = open_json_file(os.path.join(script_dir, '..', 'tools', f'{tool_name}.json'))
    tool_file_route = os.path.join(script_dir, '..', 'templates', framework, 'tools', f'{tool_name}.py')

    os.system(tool_data['package'])  # Install package
    shutil.copy(tool_file_route, f'{path or ""}/src/tools/{tool_name}.py')  # Move tool from package to project
    add_tool_to_tools_init(tool_data, path)  # Export tool from tools dir
    add_tool_to_agent_definition(framework, tool_data, path)
    insert_code_after_tag(f'{path}/.env', '# Tools', [tool_data['env']], next_line=True)  # Add env var
    insert_code_after_tag(f'{path}/.env.example', '# Tools', [tool_data['env']], next_line=True)  # Add env var

    agentstack_json = open_json_file(f'{path}/agentstack.json')
    if not agentstack_json.get('tools'):
        agentstack_json['tools'] = []
    agentstack_json['tools'].append(tool_name)
    with open(f'{path}/agentstack.json', 'w') as f:
        json.dump(agentstack_json, f, indent=4)

    print(term_color(f'🔨 Tool {tool_name} added to agentstack project successfully', 'green'))


def add_tool_to_tools_init(tool_data: dict, path: Optional[str] = None):
    file_path = f'{path or ""}/src/tools/__init__.py'
    tag = '# tool import'
    code_to_insert = [
        f"from {tool_data['name']} import {', '.join([tool_name for tool_name in tool_data['tools']])}"
    ]
    insert_code_after_tag(file_path, tag, code_to_insert, next_line=True)


def add_tool_to_agent_definition(framework: str, tool_data: dict, path: Optional[str] = None):
    filename = ''
    if framework == 'crewai':
        filename = 'src/crew.py'

    if path:
        filename = f'{path}/{filename}'

    with fileinput.input(files=filename, inplace=True) as f:
        for line in f:
            print(line.replace('tools=[', f'tools=[tools.{", tools.".join([tool_name for tool_name in tool_data["tools"]])}, '), end='')


def assert_tool_exists(tool_name: str, tools: dict):
    for cat in tools.keys():
        for tool_dict in tools[cat]:
            if tool_dict['name'] == tool_name:
                return

    print(f"\033[31mNo known AgentStack tool: '{tool_name}'\033[0m")
    sys.exit(1)

