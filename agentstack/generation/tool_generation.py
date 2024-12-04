import os, sys
from typing import Optional, Any, List
import importlib.resources
from pathlib import Path
import json
import sys
from typing import Optional, List, Dict, Union

from . import get_agent_names
from .gen_utils import insert_code_after_tag, string_in_file
from ..utils import open_json_file, get_framework, term_color
import os
import shutil
import fileinput
import ast

from agentstack import packaging
from agentstack import ValidationError
from agentstack.utils import get_package_path
from agentstack.tools import ToolConfig
from agentstack.generation import astools
from agentstack.generation.files import ConfigFile, EnvFile
from agentstack import frameworks
from .gen_utils import insert_code_after_tag, string_in_file
from ..utils import open_json_file, get_framework, term_color


# This is the filename of the location of tool imports in the user's project.
TOOLS_INIT_FILENAME: Path = Path("src/tools/__init__.py")

class ToolsInitFile(astools.File):
    """
    Modifiable AST representation of the tools init file.
    
    Use it as a context manager to make and save edits:
    ```python
    with ToolsInitFile(filename) as tools_init:
        tools_init.add_import_for_tool(...)
    ```
    """
    def get_import_for_tool(self, tool: ToolConfig) -> ast.Import:
        """
        Get the import statement for a tool.
        raises a ValidationError if the tool is imported multiple times.
        """
        all_imports = astools.get_all_imports(self.tree)
        tool_imports = [i for i in all_imports if tool.name in i.names[0].name]
        
        if len(tool_imports) > 1:
            raise ValidationError(f"Multiple imports for tool {tool.name} found in {self.filename}")
        
        try:
            return tool_imports[0]
        except IndexError:
            return None

    def add_import_for_tool(self, framework: str, tool: ToolConfig):
        """
        Add an import for a tool.
        raises a ValidationError if the tool is already imported.
        """
        tool_import = self.get_import_for_tool(tool)
        if tool_import:
            raise ValidationError(f"Tool {tool.name} already imported in {self.filename}")

        try:
            last_import = astools.get_all_imports(self.tree)[-1]
            start, end = self.get_node_range(last_import)
        except IndexError:
            start, end = 0, 0 # No imports in the file

        import_statement = tool.get_import_statement(framework)
        self.edit_node_range(end, end, f"\n{import_statement}")

    def remove_import_for_tool(self, framework: str, tool: ToolConfig):
        """
        Remove an import for a tool.
        raises a ValidationError if the tool is not imported.
        """
        tool_import = self.get_imports_for_tool(tool)
        if not tool_import:
            raise ValidationError(f"Tool {tool.name} not imported in {self.filename}")

        start, end = self.get_node_range(tool_import)
        self.edit_node_range(start, end, "")


def add_tool(tool_name: str, agents: Optional[List[str]] = [], path: Optional[str] = None):
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

    try: # Edit the user's project tool init file to include the tool
        with ToolsInitFile(path/TOOLS_INIT_FILENAME) as tools_init:
            tools_init.add_import_for_tool(tool_data)
    except ValidationError as e:
        print(term_color(f"Error adding tool:\n{e}", 'red'))
        sys.exit(1)

    # Edit the framework entrypoint file to include the tool in the agent definition
    if not len(agents): # If no agents are specified, add the tool to all agents
        agents = frameworks.get_agent_names(framework, path)
    for agent_name in agents:
        frameworks.add_tool(framework, tool_data, agent_name, path)

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


def remove_tool(tool_name: str, agents: Optional[List[str]] = [], path: Optional[str] = None):
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

    try: # Edit the user's project tool init file to exclude the tool
        with ToolsInitFile(path/TOOLS_INIT_FILENAME) as tools_init:
            tools_init.remove_import_for_tool(tool_data)
    except ValidationError as e:
        print(term_color(f"Error removing tool:\n{e}", 'red'))
        sys.exit(1)

    # Edit the framework entrypoint file to exclude the tool in the agent definition
    if not len(agents): # If no agents are specified, remove the tool from all agents
        agents = frameworks.get_agent_names(framework, path)
    for agent_name in agents:
        frameworks.remove_tool(framework, tool_data, agent_name, path)

    if tool_data.post_remove:
        os.system(tool_data.post_remove)
    # We don't remove the .env variables to preserve user data.

    with agentstack_config as config:
        config.tools.remove(tool_name)

    print(term_color(f'🔨 Tool {tool_name}', 'green'), term_color('removed', 'red'), term_color('from agentstack project successfully', 'green'))

