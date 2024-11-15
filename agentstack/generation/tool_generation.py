import importlib.resources
import json
import sys
from typing import Optional

from .gen_utils import insert_code_after_tag
from ..utils import open_json_file, get_framework, term_color
import os
import shutil
import fileinput

TOOL_INIT_FILENAME = "src/tools/__init__.py"
AGENTSTACK_JSON_FILENAME = "agentstack.json"


def add_tool(tool_name: str, path: Optional[str] = None):
    if path:
        path = path.endswith('/') and path or path + '/'
    else:
        path = './'
    with importlib.resources.path(f'agentstack.tools', 'tools.json') as tools_data_path:
        tools = open_json_file(tools_data_path)
        framework = get_framework(path)
        assert_tool_exists(tool_name, tools)
        agentstack_json = open_json_file(f'{path}{AGENTSTACK_JSON_FILENAME}')
        
        if tool_name in agentstack_json.get('tools', []):
            print(term_color(f'Tool {tool_name} is already installed', 'red'))
            sys.exit(1)

        with importlib.resources.path(f'agentstack.tools', f"{tool_name}.json") as tool_data_path:
            tool_data = open_json_file(tool_data_path)

            with importlib.resources.path(f'agentstack.templates.{framework}.tools', f"{tool_name}_tool.py") as tool_file_path:
                os.system(tool_data['package'])  # Install package
                shutil.copy(tool_file_path, f'{path}src/tools/{tool_name}_tool.py')  # Move tool from package to project
                add_tool_to_tools_init(tool_data, path)  # Export tool from tools dir
                add_tool_to_agent_definition(framework, tool_data, path)  # Add tool to agent definition
                # TODO If the tool is reinstalled .env variables will be duplicated.
                insert_code_after_tag(f'{path}.env', '# Tools', [tool_data['env']], next_line=True)  # Add env var
                insert_code_after_tag(f'{path}.env.example', '# Tools', [tool_data['env']], next_line=True)  # Add env var
                
                if not agentstack_json.get('tools'):
                    agentstack_json['tools'] = []
                agentstack_json['tools'].append(tool_name)

                with open(f'{path}{AGENTSTACK_JSON_FILENAME}', 'w') as f:
                    json.dump(agentstack_json, f, indent=4)

                print(term_color(f'🔨 Tool {tool_name} added to agentstack project successfully', 'green'))
                if tool_data.get('cta'):
                    print(term_color(f'🪩 {tool_data["cta"]}', 'blue'))


def remove_tool(tool_name: str, path: Optional[str] = None):
    if path:
        path = path.endswith('/') and path or path + '/'
    else:
        path = './'
    with importlib.resources.path(f'agentstack.tools', 'tools.json') as tools_data_path:
        tools = open_json_file(tools_data_path)
        framework = get_framework()
        assert_tool_exists(tool_name, tools)
        agentstack_json = open_json_file(f'{path}{AGENTSTACK_JSON_FILENAME}')
        
        if not tool_name in agentstack_json.get('tools', []):
            print(term_color(f'Tool {tool_name} is not installed', 'red'))
            sys.exit(1)

        with importlib.resources.path(f'agentstack.tools', f"{tool_name}.json") as tool_data_path:
            tool_data = open_json_file(tool_data_path)
            os.remove(f'{path}src/tools/{tool_name}_tool.py')
            remove_tool_from_tools_init(tool_data, path)
            remove_tool_from_agent_definition(framework, tool_data, path)
            # We don't remove the .env variables to preserve user data.
            
            agentstack_json['tools'].remove(tool_name)
            with open(f'{path}{AGENTSTACK_JSON_FILENAME}', 'w') as f:
                json.dump(agentstack_json, f, indent=4)
            
            print(term_color(f'🔨 Tool {tool_name} removed from agentstack project successfully', 'green'))
            # TODO If we add an uninstall command to the tool_config json we can run it instead. 
            print(term_color(f'To uninstall dependencies, reverse the install command: {tool_data["package"]}', 'blue'))


def _format_tool_import_statement(tool_data: dict):
    return f"from .{tool_data['name']}_tool import {', '.join([tool_name for tool_name in tool_data['tools']])}"


def add_tool_to_tools_init(tool_data: dict, path: str = ''):
    file_path = f'{path}{TOOL_INIT_FILENAME}'
    tag = '# tool import'
    code_to_insert = [_format_tool_import_statement(tool_data), ]
    insert_code_after_tag(file_path, tag, code_to_insert, next_line=True)


def remove_tool_from_tools_init(tool_data: dict, path: str = ''):
    """Search for the import statement in the init and remove it."""
    file_path = f'{path}{TOOL_INIT_FILENAME}'
    import_statement = _format_tool_import_statement(tool_data)
    with fileinput.input(files=file_path, inplace=True) as f:
        for line in f:
            if line.strip() != import_statement:
                print(line, end='')


def _framework_filename(framework: str, path: str = ''):
    if framework == 'crewai':
        return f'{path}src/crew.py'

    print(term_color(f'Unknown framework: {framework}', 'red'))
    sys.exit(1)


def add_tool_to_agent_definition(framework: str, tool_data: dict, path: str = ''):
    filename = _framework_filename(framework, path)
    with fileinput.input(files=filename, inplace=True) as f:
        for line in f:
            print(line.replace('tools=[', f'tools=[{"*" if tool_data.get("tools_bundled") else ""}tools.{", tools.".join([tool_name for tool_name in tool_data["tools"]])}, '), end='')


def remove_tool_from_agent_definition(framework: str, tool_data: dict, path: str = ''):
    filename = _framework_filename(framework, path)
    with fileinput.input(files=filename, inplace=True) as f:
        for line in f:
            print(line.replace(f'{", ".join([f"tools.{tool_name}" for tool_name in tool_data["tools"]])}, ', ''), end='')


def assert_tool_exists(tool_name: str, tools: dict):
    for cat in tools.keys():
        for tool_dict in tools[cat]:
            if tool_dict['name'] == tool_name:
                return

    print(term_color(f'No known agentstack tool: {tool_name}', 'red'))
    sys.exit(1)

