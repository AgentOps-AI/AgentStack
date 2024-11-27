import importlib.resources
import json
import sys
from typing import Optional, List, Dict, Union

from . import get_agent_names
from .gen_utils import insert_code_after_tag, string_in_file, _framework_filename
from ..utils import open_json_file, get_framework, term_color
import os
import shutil
import fileinput
import astor
import ast

TOOL_INIT_FILENAME = "src/tools/__init__.py"
AGENTSTACK_JSON_FILENAME = "agentstack.json"


def add_tool(tool_name: str, path: Optional[str] = None, agents: Optional[List[str]] = []):
    if path:
        path = path.endswith('/') and path or path + '/'
    else:
        path = './'
    with importlib.resources.path(f'agentstack.tools', 'tools.json') as tools_data_path:
        tools = open_json_file(tools_data_path)
        framework = get_framework(path)
        assert_tool_exists(tool_name, tools)
        agentstack_json = open_json_file(f'{path}{AGENTSTACK_JSON_FILENAME}')

        # if tool_name in agentstack_json.get('tools', []):
        #     print(term_color(f'Tool {tool_name} is already installed', 'red'))
        #     sys.exit(1)

        with importlib.resources.path(f'agentstack.tools', f"{tool_name}.json") as tool_data_path:
            tool_data = open_json_file(tool_data_path)

            with importlib.resources.path(f'agentstack.templates.{framework}.tools',
                                          f"{tool_name}_tool.py") as tool_file_path:
                if tool_data.get('packages'):
                    if os.system(f"poetry add {' '.join(tool_data['packages'])}") == 1: # Install packages
                        print(term_color("AgentStack: Failed to install tool requirements. Please resolve dependency issues and try again,", 'red'))
                        return
                shutil.copy(tool_file_path, f'{path}src/tools/{tool_name}_tool.py')  # Move tool from package to project
                add_tool_to_tools_init(tool_data, path)  # Export tool from tools dir
                add_tool_to_agent_definition(framework, tool_data, path, agents)  # Add tool to agent definition
                if tool_data.get('env'): # if the env vars aren't in the .env files, add them
                    first_var_name = tool_data['env'].split('=')[0]
                    if not string_in_file(f'{path}.env', first_var_name):
                        insert_code_after_tag(f'{path}.env', '# Tools', [tool_data['env']], next_line=True)  # Add env var
                    if not string_in_file(f'{path}.env.example', first_var_name):
                        insert_code_after_tag(f'{path}.env.example', '# Tools', [tool_data['env']], next_line=True)  # Add env var

                if not agentstack_json.get('tools'):
                    agentstack_json['tools'] = []
                if tool_name not in agentstack_json['tools']:
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
            if tool_data.get('packages'):
                os.system(f"poetry remove {' '.join(tool_data['packages'])}") # Uninstall packages
            os.remove(f'{path}src/tools/{tool_name}_tool.py')
            remove_tool_from_tools_init(tool_data, path)
            remove_tool_from_agent_definition(framework, tool_data, path)
            # We don't remove the .env variables to preserve user data.

            agentstack_json['tools'].remove(tool_name)
            with open(f'{path}{AGENTSTACK_JSON_FILENAME}', 'w') as f:
                json.dump(agentstack_json, f, indent=4)

            print(term_color(f'🔨 Tool {tool_name}', 'green'), term_color('removed', 'red'), term_color('from agentstack project successfully', 'green'))


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


def add_tool_to_agent_definition(framework: str, tool_data: dict, path: str = '', agents: list[str] = []):
    """
        Add tools to specific agent definitions using AST transformation.

        Args:
            framework: Name of the framework
            tool_data: Dictionary containing tool information
                {
                    "tools": List[str],  # List of tool names to add
                    "tools_bundled": bool  # Whether to include tools.*
                }
            agents: Optional list of agent names to modify. If None, modifies all agents.
            path: Optional path to the framework file
        """
    modify_agent_tools(framework, tool_data, 'add', agents, path, 'tools')


def remove_tool_from_agent_definition(framework: str, tool_data: dict, path: str = ''):
    modify_agent_tools(framework, tool_data, 'remove', None, path, 'tools')


def assert_tool_exists(tool_name: str, tools: dict):
    for cat in tools.keys():
        for tool_dict in tools[cat]:
            if tool_dict['name'] == tool_name:
                return

    print(term_color(f'No known agentstack tool: {tool_name}', 'red'))
    sys.exit(1)


def _create_tool_attribute(tool_name: str, base_name: str = 'tools') -> ast.Attribute:
    """Create an AST node for a tool attribute"""
    return ast.Attribute(
        value=ast.Name(id=base_name, ctx=ast.Load()),
        attr=tool_name,
        ctx=ast.Load()
    )

def _create_starred_tool(tool_name: str, base_name: str = 'tools') -> ast.Starred:
    """Create an AST node for a starred tool expression"""
    return ast.Starred(
        value=ast.Attribute(
            value=ast.Name(id=base_name, ctx=ast.Load()),
            attr=tool_name,
            ctx=ast.Load()
        ),
        ctx=ast.Load()
    )


def _create_tool_attributes(
        tool_names: List[str],
        base_name: str = 'tools'
) -> List[ast.Attribute]:
    """Create AST nodes for multiple tool attributes"""
    return [_create_tool_attribute(name, base_name) for name in tool_names]


def _create_tool_nodes(
    tool_names: List[str],
    is_bundled: bool = False,
    base_name: str = 'tools'
) -> List[Union[ast.Attribute, ast.Starred]]:
    """Create AST nodes for multiple tool attributes"""
    return [
        _create_starred_tool(name, base_name) if is_bundled
        else _create_tool_attribute(name, base_name)
        for name in tool_names
    ]


def _is_tool_node_match(node: ast.AST, tool_name: str, base_name: str = 'tools') -> bool:
    """
    Check if an AST node matches a tool reference, regardless of whether it's starred

    Args:
        node: AST node to check (can be Attribute or Starred)
        tool_name: Name of the tool to match
        base_name: Base module name (default: 'tools')

    Returns:
        bool: True if the node matches the tool reference
    """
    # If it's a Starred node, check its value
    if isinstance(node, ast.Starred):
        node = node.value

    # Extract the attribute name and base regardless of node type
    if isinstance(node, ast.Attribute):
        is_base_match = (isinstance(node.value, ast.Name) and
                         node.value.id == base_name)
        is_name_match = node.attr == tool_name
        return is_base_match and is_name_match

    return False


def _process_tools_list(
        current_tools: List[ast.AST],
        tool_data: Dict,
        operation: str,
        base_name: str = 'tools'
) -> List[ast.AST]:
    """
    Process a tools list according to the specified operation.

    Args:
        current_tools: Current list of tool nodes
        tool_data: Tool configuration dictionary
        operation: Operation to perform ('add' or 'remove')
        base_name: Base module name for tools
    """
    if operation == 'add':
        new_tools = current_tools.copy()
        # Add new tools with bundling if specified
        new_tools.extend(_create_tool_nodes(
            tool_data["tools"],
            tool_data.get("tools_bundled", False),
            base_name
        ))
        return new_tools

    elif operation == 'remove':
        # Filter out tools that match any in the removal list
        return [
            tool for tool in current_tools
            if not any(_is_tool_node_match(tool, name, base_name)
                       for name in tool_data["tools"])
        ]

    raise ValueError(f"Unsupported operation: {operation}")


def _modify_agent_tools(
        node: ast.FunctionDef,
        tool_data: Dict,
        operation: str,
        agents: Optional[List[str]] = None,
        base_name: str = 'tools'
) -> ast.FunctionDef:
    """
    Modify the tools list in an agent definition.

    Args:
        node: AST node of the function to modify
        tool_data: Tool configuration dictionary
        operation: Operation to perform ('add' or 'remove')
        agents: Optional list of agent names to modify
        base_name: Base module name for tools
    """
    # Skip if not in specified agents list
    if agents is not None and node.name not in agents:
        return node

    # Check if this is an agent-decorated function
    if not any(isinstance(d, ast.Name) and d.id == 'agent'
               for d in node.decorator_list):
        return node

    # Find the Return statement and modify tools
    for item in node.body:
        if isinstance(item, ast.Return):
            agent_call = item.value
            if isinstance(agent_call, ast.Call):
                for kw in agent_call.keywords:
                    if kw.arg == 'tools':
                        if isinstance(kw.value, ast.List):
                            # Process the tools list
                            new_tools = _process_tools_list(
                                kw.value.elts,
                                tool_data,
                                operation,
                                base_name
                            )

                            # Replace with new list
                            kw.value = ast.List(elts=new_tools, ctx=ast.Load())

    return node


def modify_agent_tools(
        framework: str,
        tool_data: Dict,
        operation: str,
        agents: Optional[List[str]] = None,
        path: str = '',
        base_name: str = 'tools'
) -> None:
    """
    Modify tools in agent definitions using AST transformation.

    Args:
        framework: Name of the framework
        tool_data: Dictionary containing tool information
            {
                "tools": List[str],  # List of tool names
                "tools_bundled": bool  # Whether to include tools.* (for add operation)
            }
        operation: Operation to perform ('add' or 'remove')
        agents: Optional list of agent names to modify
        path: Optional path to the framework file
        base_name: Base module name for tools (default: 'tools')
    """
    if agents is not None:
        valid_agents = get_agent_names(path=path)
        for agent in agents:
            if agent not in valid_agents:
                print(term_color(f"Agent '{agent}' not found in the project.", 'red'))
                sys.exit(1)

    filename = _framework_filename(framework, path)

    with open(filename, 'r') as f:
        source = f.read()

    tree = ast.parse(source)

    class ModifierTransformer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            return _modify_agent_tools(node, tool_data, operation, agents, base_name)

    modified_tree = ModifierTransformer().visit(tree)
    modified_source = astor.to_source(modified_tree)

    with open(filename, 'w') as f:
        f.write(modified_source)