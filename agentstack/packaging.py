"""
packaging
=========
Packaging, in our context, is management of tools and dependencies inside an
agentstack project. This module provides functions to install, remove, and
upgrade tools and install dependencies.
"""
import os, sys
import shutil
from typing import TYPE_CHECKING, Optional
from packaging.metadata import Metadata
from agentstack.utils import term_color, get_package_path, get_framework
if TYPE_CHECKING: # TODO move ToolConfig to a separate file
    from agentstack.generation.tool_generation import ToolConfig

class PackageManager:
    cmd: str
    install: str
    update: str
    
    def __init__(self, cmd: str, install: str, update: str):
        self.cmd, self.install, self.update = cmd, install, update
    
    def install(self, *args):
        os.system(f"{self.cmd} {self.install} {' '.join(args)}")
    
    def upgrade(self, *args):
        os.system(f"{self.cmd} {self.update} {' '.join(args)}")

    def install_tool(self, tool: 'ToolConfig', framework: str, path: Optional[str] = None):
        """
        Copy a tool's source files from the agentstack install directory to the app 
        tools directory and install relevant dependencies. 
        
        `tool` is a ToolConfig object representing the tool to be installed.
        `framework` is the framework of the app which will be used to select the
            relevant `opional-dependencies`.
        `path` is the path to the app directory. If `None`, the current working directory.
        """
        raise NotImplementedError

    def remove_tool(self, tool: 'ToolConfig', path: Optional[str] = None):
        """
        Remove a tool's source files from the app tools directory.
        
        `tool` is a ToolConfig object representing the tool to be removed.
        `path` is the path to the app directory. If `None`, the current working directory.
        """
        shutil.rmtree(tool.get_path())

class UV(PackageManager):
    def __init__(self):
        super().__init__('uv', 'add', 'pip install --upgrade')
    
    def install_tool(self, tool: 'ToolConfig', path: Optional[str] = None):
        # uv pip install --directory <tool directory> --target <app tools directory> --link-mode copy <tool name> --editable .[<framework>]
        os.system(f"{self.cmd} pip install --link-mode copy --directory {tool.get_path()} --target {path}src/tools/ --editable .[{framework}]")

class Poetry(PackageManager):
    def __init__(self):
        super().__init__('poetry', 'add', 'update')
    
    def install_tool(self, tool: 'ToolConfig', framework: str, path: Optional[str] = None):
        # poetry doesn't have a way to install into a target directory afaik so we
        # first install the dependencies and then manually copy the tool files
        # poetry install --no-root --directory <package_path> --with <optional_dependencies_tags>
        arg = f' --directory {package_path}'
        if optional_dependencies_tag:
            arg += f" --with {','.join(optional_dependencies_tags)}"
        os.system(f"{self.cmd} install --no-root {arg}")
        shutil.copytree(tool.get_path(), f"{path}src/tools/{tool.name}")

class PIP(PackageManager):
    def __init__(self):
        super().__init__('pip', 'install', 'install --upgrade')
    
    def install_tool(self, tool: 'ToolConfig', framework: str, path: Optional[str] = None):
        # pip install --target <app tools directory> --editable .[<framework>]
        os.system(f"{self.cmd} {self.install} --target {path}src/tools/ --editable {tool.get_path()}[{framework}]")

UV = UV()
POETRY =  Poetry()
PIP = PIP()

PACKAGE_MAGANAGERS = [UV, POETRY, PIP] # in order of preference

def detect_package_manager() -> PackageManager:
    # TODO use package manager specified in agentstack.json
    # TODO what about `path`
    # if ConfigFile(path).package_manager:
    #     for manager in PACKAGE_MANAGERS:
    #         if manager.cmd == ConfigFile.package_manager:
    #             return manager

    # detect best installed package manager
    for manager in PACKAGE_MANAGERS:
        if shutil.which(manager.cmd):
            return manager
    
    print(term_color('No package manager detected', 'red'))
    print('Install one of the following package managers: ', end='')
    print(', '.join(manager.cmd for manager in PACKAGE_MANAGERS))
    sys.exit(1)

def install(package: str):
    detect_package_manager().install(package)

def upgrade(package: str):
    detect_package_manager().upgrade(package)

def get_tool_metadata(tool: 'ToolConfig') -> Metadata:
    """
    Parsed pyproject.toml for the tool
    NOTE Does not include `dependencies` or `optional-dependencies`
    """
    return Metadata.from_pyproject(get_tool_path()/'pyproject.toml')

def install_tool(tool: 'ToolConfig', path: Optional[str] = None):
    """
    Copy a tool's applicable source files and install relevant dependencies
    """
    framework = get_framework(path)
    manager = detect_package_manager()
    manager.install_tool(tool, framework, path)

def remove_tool(tool: 'ToolConfig', path: Optional[str] = None):
    """
    Remove a tool's source files.
    Removing dependencies is messy, so we just leave them installed. 
    """
    manager = detect_package_manager()
    manager.remove_tool(tool, path)

