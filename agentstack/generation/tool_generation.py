import os, sys
from typing import Optional, Any, List
import importlib.resources
from pathlib import Path
import json
import shutil
import fileinput
from pydantic import BaseModel, ValidationError

from .gen_utils import insert_code_after_tag, string_in_file
from ..utils import open_json_file, get_framework, term_color


TOOL_INIT_FILENAME = "src/tools/__init__.py"
AGENTSTACK_JSON_FILENAME = "agentstack.json"
FRAMEWORK_FILENAMES: dict[str, str] = {
    'crewai': 'src/crew.py', 
}

def get_package_path() -> Path:
    if sys.version_info <= (3, 9):
        return Path(sys.modules['agentstack'].__path__[0])
    return importlib.resources.files('agentstack')

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

def add_tool(tool_name: str, path: Optional[str] = None):
    if path:
        path = path.endswith('/') and path or path + '/'
    else:
        path = './'
    
    framework = get_framework(path)
    agentstack_json = open_json_file(f'{path}{AGENTSTACK_JSON_FILENAME}')
    
    if tool_name in agentstack_json.get('tools', []):
        print(term_color(f'Tool {tool_name} is already installed', 'red'))
        sys.exit(1)

    tool_data = ToolConfig.from_tool_name(tool_name)
    tool_file_path = tool_data.get_impl_file_path(framework)
    if tool_data.packages:
        os.system(f"poetry add {' '.join(tool_data.packages)}")  # Install packages
    shutil.copy(tool_file_path, f'{path}src/tools/{tool_name}_tool.py')  # Move tool from package to project
    add_tool_to_tools_init(tool_data, path)  # Export tool from tools dir
    add_tool_to_agent_definition(framework, tool_data, path)  # Add tool to agent definition
    if tool_data.env: # if the env vars aren't in the .env files, add them
        # tool_data.env is a dict, key is the env var name, value is the value
        for var, value in tool_data.env.items():
            env_var = f'{var}={value}'
            if not string_in_file(f'{path}.env', env_var):
                insert_code_after_tag(f'{path}.env', '# Tools', [env_var, ])
            if not string_in_file(f'{path}.env.example', env_var):
                insert_code_after_tag(f'{path}.env.example', '# Tools', [env_var, ])
    
    if tool_data.post_install:
        os.system(tool_data.post_install)
    
    if not agentstack_json.get('tools'):
        agentstack_json['tools'] = []
    agentstack_json['tools'].append(tool_name)

    with open(f'{path}{AGENTSTACK_JSON_FILENAME}', 'w') as f:
        json.dump(agentstack_json, f, indent=4)

    print(term_color(f'🔨 Tool {tool_name} added to agentstack project successfully', 'green'))
    if tool_data.cta:
        print(term_color(f'🪩 {tool_data.cta}', 'blue'))

def remove_tool(tool_name: str, path: Optional[str] = None):
    if path:
        path = path.endswith('/') and path or path + '/'
    else:
        path = './'
    
    framework = get_framework()
    agentstack_json = open_json_file(f'{path}{AGENTSTACK_JSON_FILENAME}')
    
    if not tool_name in agentstack_json.get('tools', []):
        print(term_color(f'Tool {tool_name} is not installed', 'red'))
        sys.exit(1)

    tool_data = ToolConfig.from_tool_name(tool_name)
    if tool_data.packages:
        os.system(f"poetry remove {' '.join(tool_data.packages)}") # Uninstall packages
    try:
        os.remove(f'{path}src/tools/{tool_name}_tool.py')
    except FileNotFoundError:
        print(f'"src/tools/{tool_name}_tool.py" not found')
    remove_tool_from_tools_init(tool_data, path)
    remove_tool_from_agent_definition(framework, tool_data, path)
    if tool_data.post_remove:
        os.system(tool_data.post_remove)
    # We don't remove the .env variables to preserve user data.
    
    agentstack_json['tools'].remove(tool_name)
    with open(f'{path}{AGENTSTACK_JSON_FILENAME}', 'w') as f:
        json.dump(agentstack_json, f, indent=4)
    
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

def add_tool_to_agent_definition(framework: str, tool_data: ToolConfig, path: str = ''):
    with fileinput.input(files=get_framework_filename(framework, path), inplace=True) as f:
        for line in f:
            print(line.replace('tools=[', f'tools=[{"*" if tool_data.tools_bundled else ""}tools.{", tools.".join(tool_data.tools)}, '), end='')

def remove_tool_from_agent_definition(framework: str, tool_data: ToolConfig, path: str = ''):
    with fileinput.input(files=get_framework_filename(framework, path), inplace=True) as f:
        for line in f:
            print(line.replace(f'{", ".join([f"tools.{name}" for name in tool_data.tools])}, ', ''), end='')

