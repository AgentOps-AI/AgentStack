import os, sys
from typing import Optional, Any, List
import importlib.resources
from pathlib import Path
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
from pydantic import BaseModel, ValidationError

from agentstack import packaging
from agentstack.utils import get_package_path
from agentstack.generation.files import ConfigFile, EnvFile
from .gen_utils import insert_code_after_tag, string_in_file
from ..utils import open_json_file, get_framework, term_color


TOOL_INIT_FILENAME = "src/tools/__init__.py"
FRAMEWORK_FILENAMES: dict[str, str] = {
    'crewai': 'src/crew.py',
}

def get_framework_filename(framework: str, path: str = ''):
    if path:
        path = path.endswith('/') and path or path + '/'
    else:
        path = './'
    try:
        return f"{path}{FRAMEWORK_FILENAMES[framework]}"
    except KeyError:
        print(term_color(f'Unknown framework: {framework}', 'red'))
        sys.exit(1)

class ToolConfig(BaseModel):
    name: str
    category: str
    tools: list[str]
    url: Optional[str] = None
    tools_bundled: bool = False
    cta: Optional[str] = None
    env: Optional[dict] = None
    packages: Optional[List[str]] = None
    post_install: Optional[str] = None
    post_remove: Optional[str] = None

    @classmethod
    def from_tool_name(cls, name: str) -> 'ToolConfig':
        path = get_package_path() / f'tools/{name}.json'
        if not os.path.exists(path):
            print(term_color(f'No known agentstack tool: {name}', 'red'))
            sys.exit(1)
        return cls.from_json(path)

    @classmethod
    def from_json(cls, path: Path) -> 'ToolConfig':
        data = open_json_file(path)
        try:
            return cls(**data)
        except ValidationError as e:
            print(term_color(f"Error validating tool config JSON: \n{path}", 'red'))
            for error in e.errors():
                print(f"{' '.join(error['loc'])}: {error['msg']}")
            sys.exit(1)

    def get_import_statement(self) -> str:
        return f"from .{self.name}_tool import {', '.join(self.tools)}"

    def get_impl_file_path(self, framework: str) -> Path:
        return get_package_path() / f'templates/{framework}/tools/{self.name}_tool.py'

def get_all_tool_paths() -> list[Path]:
    paths = []
    tools_dir = get_package_path() / 'tools'
    for file in tools_dir.iterdir():
        if file.is_file() and file.suffix == '.json':
            paths.append(file)
    return paths

def get_all_tool_names() -> list[str]:
    return [path.stem for path in get_all_tool_paths()]

def get_all_tools() -> list[ToolConfig]:
    return [ToolConfig.from_json(path) for path in get_all_tool_paths()]

def add_tool(tool_name: str, path: Optional[str] = None, agents: Optional[List[str]] = []):
    if path:
        path = path.endswith('/') and path or path + '/'
    else:
        path = './'

    framework = get_framework(path)
    agentstack_config = ConfigFile(path)

    if tool_name in agentstack_config.tools:
        print(term_color(f'Tool {tool_name} is already installed', 'red'))
        sys.exit(1)

    tool_data = ToolConfig.from_tool_name(tool_name)
    tool_file_path = tool_data.get_impl_file_path(framework)

    if tool_data.packages:
        packaging.install(' '.join(tool_data.packages))
    shutil.copy(tool_file_path, f'{path}src/tools/{tool_name}_tool.py')  # Move tool from package to project
    add_tool_to_tools_init(tool_data, path)  # Export tool from tools dir
    add_tool_to_agent_definition(framework=framework, tool_data=tool_data, path=path, agents=agents)  # Add tool to agent definition

    if tool_data.env: # add environment variables which don't exist
        with EnvFile(path) as env:
            for var, value in tool_data.env.items():
                env.append_if_new(var, value)
        with EnvFile(path, filename=".env.example") as env:
            for var, value in tool_data.env.items():
                env.append_if_new(var, value)

    if tool_data.post_install:
        os.system(tool_data.post_install)

    with agentstack_config as config:
        config.tools.append(tool_name)

    print(term_color(f'🔨 Tool {tool_name} added to agentstack project successfully', 'green'))
    if tool_data.cta:
        print(term_color(f'🪩 {tool_data.cta}', 'blue'))


def remove_tool(tool_name: str, path: Optional[str] = None):
    if path:
        path = path.endswith('/') and path or path + '/'
    else:
        path = './'

    framework = get_framework()
    agentstack_config = ConfigFile(path)

    if not tool_name in agentstack_config.tools:
        print(term_color(f'Tool {tool_name} is not installed', 'red'))
        sys.exit(1)

    tool_data = ToolConfig.from_tool_name(tool_name)
    if tool_data.packages:
        packaging.remove(' '.join(tool_data.packages))
    try:
        os.remove(f'{path}src/tools/{tool_name}_tool.py')
    except FileNotFoundError:
        print(f'"src/tools/{tool_name}_tool.py" not found')
    remove_tool_from_tools_init(tool_data, path)
    remove_tool_from_agent_definition(framework, tool_data, path)
    if tool_data.post_remove:
        os.system(tool_data.post_remove)
    # We don't remove the .env variables to preserve user data.

    with agentstack_config as config:
        config.tools.remove(tool_name)

    print(term_color(f'🔨 Tool {tool_name}', 'green'), term_color('removed', 'red'), term_color('from agentstack project successfully', 'green'))


def add_tool_to_tools_init(tool_data: ToolConfig, path: str = ''):
    file_path = f'{path}{TOOL_INIT_FILENAME}'
    tag = '# tool import'
    code_to_insert = [tool_data.get_import_statement(), ]
    insert_code_after_tag(file_path, tag, code_to_insert, next_line=True)


def remove_tool_from_tools_init(tool_data: ToolConfig, path: str = ''):
    """Search for the import statement in the init and remove it."""
    file_path = f'{path}{TOOL_INIT_FILENAME}'
    import_statement = tool_data.get_import_statement()
    with fileinput.input(files=file_path, inplace=True) as f:
        for line in f:
            if line.strip() != import_statement:
                print(line, end='')


def add_tool_to_agent_definition(framework: str, tool_data: ToolConfig, path: str = '', agents: list[str] = []):
    """
        Add tools to specific agent definitions using AST transformation.

        Args:
            framework: Name of the framework
            tool_data: ToolConfig
            agents: Optional list of agent names to modify. If None, modifies all agents.
            path: Optional path to the framework file
        """
    modify_agent_tools(framework=framework, tool_data=tool_data, operation='add', agents=agents, path=path, base_name='tools')


def remove_tool_from_agent_definition(framework: str, tool_data: ToolConfig, path: str = ''):
    modify_agent_tools(framework=framework, tool_data=tool_data, operation='remove', agents=None, path=path, base_name='tools')


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
        tool_data: ToolConfig,
        operation: str,
        base_name: str = 'tools'
) -> List[ast.AST]:
    """
    Process a tools list according to the specified operation.

    Args:
        current_tools: Current list of tool nodes
        tool_data: Tool configuration
        operation: Operation to perform ('add' or 'remove')
        base_name: Base module name for tools
    """
    if operation == 'add':
        new_tools = current_tools.copy()
        # Add new tools with bundling if specified
        new_tools.extend(_create_tool_nodes(
            tool_data.tools,
            tool_data.tools_bundled,
            base_name
        ))
        return new_tools

    elif operation == 'remove':
        # Filter out tools that match any in the removal list
        return [
            tool for tool in current_tools
            if not any(_is_tool_node_match(tool, name, base_name)
                       for name in tool_data.tools)
        ]

    raise ValueError(f"Unsupported operation: {operation}")


def _modify_agent_tools(
        node: ast.FunctionDef,
        tool_data: ToolConfig,
        operation: str,
        agents: Optional[List[str]] = None,
        base_name: str = 'tools'
) -> ast.FunctionDef:
    """
    Modify the tools list in an agent definition.

    Args:
        node: AST node of the function to modify
        tool_data: Tool configuration
        operation: Operation to perform ('add' or 'remove')
        agents: Optional list of agent names to modify
        base_name: Base module name for tools
    """
    # Skip if not in specified agents list
    if agents is not None and agents != []:
        if node.name not in agents:
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
        tool_data: ToolConfig,
        operation: str,
        agents: Optional[List[str]] = None,
        path: str = '',
        base_name: str = 'tools'
) -> None:
    """
    Modify tools in agent definitions using AST transformation.

    Args:
        framework: Name of the framework
        tool_data: ToolConfig
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

    with open(filename, 'r', encoding='utf-8') as f:
        source_lines = f.readlines()

    # Create a map of line numbers to comments
    comments = {}
    for i, line in enumerate(source_lines):
        stripped = line.strip()
        if stripped.startswith('#'):
            comments[i + 1] = line

    tree = ast.parse(''.join(source_lines))

    class ModifierTransformer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            return _modify_agent_tools(node, tool_data, operation, agents, base_name)

    modified_tree = ModifierTransformer().visit(tree)
    modified_source = astor.to_source(modified_tree)
    modified_lines = modified_source.splitlines()

    # Reinsert comments
    final_lines = []
    for i, line in enumerate(modified_lines, 1):
        if i in comments:
            final_lines.append(comments[i])
        final_lines.append(line + '\n')

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(''.join(final_lines))