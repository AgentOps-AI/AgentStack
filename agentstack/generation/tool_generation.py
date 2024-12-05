import os, sys
from typing import Optional, Union, Any
from pathlib import Path
import shutil
import fileinput
import ast

from agentstack import frameworks
from agentstack import packaging
from agentstack import ValidationError
from agentstack.utils import term_color
from agentstack.tools import ToolConfig
from agentstack.generation import asttools
from agentstack.generation.files import ConfigFile, EnvFile


# This is the filename of the location of tool imports in the user's project.
TOOLS_INIT_FILENAME: Path = Path("src/tools/__init__.py")

class ToolsInitFile(asttools.File):
    """
    Modifiable AST representation of the tools init file.
    
    Use it as a context manager to make and save edits:
    ```python
    with ToolsInitFile(filename) as tools_init:
        tools_init.add_import_for_tool(...)
    ```
    """
    def get_import_for_tool(self, tool: ToolConfig) -> Union[ast.Import, ast.ImportFrom]:
        """
        Get the import statement for a tool.
        raises a ValidationError if the tool is imported multiple times.
        """
        all_imports = asttools.get_all_imports(self.tree)
        tool_imports = [i for i in all_imports if tool.module_name == i.module]
        
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
            last_import = asttools.get_all_imports(self.tree)[-1]
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
        tool_import = self.get_import_for_tool(tool)
        if not tool_import:
            raise ValidationError(f"Tool {tool.name} not imported in {self.filename}")

        start, end = self.get_node_range(tool_import)
        self.edit_node_range(start, end, "")


def add_tool(tool_name: str, agents: Optional[list[str]] = [], path: Optional[Path] = None):
    if path is None: path = Path()
    agentstack_config = ConfigFile(path)
    framework = agentstack_config.framework

    if tool_name in agentstack_config.tools:
        print(term_color(f'Tool {tool_name} is already installed', 'red'))
        sys.exit(1)

    tool = ToolConfig.from_tool_name(tool_name)
    tool_file_path = tool.get_impl_file_path(framework)

    if tool.packages:
        packaging.install(' '.join(tool.packages))
    
    # Move tool from package to project
    shutil.copy(tool_file_path, path/f'src/tools/{tool.module_name}.py')

    try: # Edit the user's project tool init file to include the tool
        with ToolsInitFile(path/TOOLS_INIT_FILENAME) as tools_init:
            tools_init.add_import_for_tool(framework, tool)
    except ValidationError as e:
        print(term_color(f"Error adding tool:\n{e}", 'red'))

    # Edit the framework entrypoint file to include the tool in the agent definition
    if not agents: # If no agents are specified, add the tool to all agents
        agents = frameworks.get_agent_names(framework, path)
    for agent_name in agents:
        frameworks.add_tool(framework, tool, agent_name, path)

    if tool.env: # add environment variables which don't exist
        with EnvFile(path) as env:
            for var, value in tool.env.items():
                env.append_if_new(var, value)
        with EnvFile(path, filename=".env.example") as env:
            for var, value in tool.env.items():
                env.append_if_new(var, value)

    if tool.post_install:
        os.system(tool.post_install)

    with agentstack_config as config:
        config.tools.append(tool.name)

    print(term_color(f'🔨 Tool {tool.name} added to agentstack project successfully', 'green'))
    if tool.cta:
        print(term_color(f'🪩  {tool.cta}', 'blue'))


def remove_tool(tool_name: str, agents: Optional[list[str]] = [], path: Optional[Path] = None):
    if path is None: path = Path()
    agentstack_config = ConfigFile(path)
    framework = agentstack_config.framework

    if not tool_name in agentstack_config.tools:
        print(term_color(f'Tool {tool_name} is not installed', 'red'))
        sys.exit(1)

    tool = ToolConfig.from_tool_name(tool_name)
    if tool.packages:
        packaging.remove(' '.join(tool.packages))

    # TODO ensure that other agents in the project are not using the tool. 
    try:
        os.remove(path/f'src/tools/{tool.module_name}.py')
    except FileNotFoundError:
        print(f'"src/tools/{tool.module_name}.py" not found')

    try: # Edit the user's project tool init file to exclude the tool
        with ToolsInitFile(path/TOOLS_INIT_FILENAME) as tools_init:
            tools_init.remove_import_for_tool(framework, tool)
    except ValidationError as e:
        print(term_color(f"Error removing tool:\n{e}", 'red'))

    # Edit the framework entrypoint file to exclude the tool in the agent definition
    if not agents: # If no agents are specified, remove the tool from all agents
        agents = frameworks.get_agent_names(framework, path)
    for agent_name in agents:
        frameworks.remove_tool(framework, tool, agent_name, path)

    if tool.post_remove:
        os.system(tool.post_remove)
    # We don't remove the .env variables to preserve user data.

    with agentstack_config as config:
        config.tools.remove(tool.name)

    print(term_color(f'🔨 Tool {tool_name}', 'green'), term_color('removed', 'red'), 
        term_color('from agentstack project successfully', 'green'))

