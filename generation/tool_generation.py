import sys

from generation.gen_utils import insert_code_after_tag
from utils import snake_to_camel, open_json_file, get_framework
import os
import shutil


def add_tool(tool_name: str):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tools = open_json_file(os.path.join(script_dir, '..', 'tools', 'tools.json'))
    framework = get_framework()
    assert_tool_exists(tool_name, tools)

    tool_data = open_json_file(os.path.join(script_dir, '..', 'tools', f'{tool_name}.json'))
    tool_file_route = os.path.join(script_dir, '..', 'templates', framework, 'tools', f'{tool_name}.py')

    os.system(tool_data['package'])  # Install package
    # Move tool from package to project
    shutil.copy(tool_file_route, f'src/tools/{tool_name}.py')
    add_tool_to_tools_init(tool_name)  # Export tool from tools dir
    insert_code_after_tag('.env', '# Tools', [tool_data['env']])  # Add env var
    insert_code_after_tag('.env.example', '# Tools', [tool_data['env']])  # Add env var


def add_tool_to_tools_init(tool_name: str):
    file_path = 'src/tools/__init__.py'
    tag = '# tool import'
    code_to_insert = [
        f"from {tool_name} import {snake_to_camel(tool_name)}"
    ]
    insert_code_after_tag(file_path, tag, code_to_insert)


def assert_tool_exists(tool_name: str, tools: dict):
    for cat in tools.keys():
        for tool_dict in tools[cat]:
            if tool_dict['name'] == tool_name:
                return

    print(f"\033[31mNo known AgentStack tool: '{tool_name}'\033[0m")
    sys.exit(1)

