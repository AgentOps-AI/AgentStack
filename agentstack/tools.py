from typing import Optional
import os, sys
from pathlib import Path
import pydantic
from agentstack.utils import get_package_path, open_json_file, term_color


class ToolConfig(pydantic.BaseModel):
    """
    This represents the configuration data for a tool.
    It parses and validates the `config.json` file for a tool.
    """
    name: str
    category: str
    tools: list[str]
    url: Optional[str] = None
    tools_bundled: bool = False
    cta: Optional[str] = None
    env: Optional[dict] = None
    packages: Optional[list[str]] = None
    post_install: Optional[str] = None
    post_remove: Optional[str] = None

    @classmethod
    def from_tool_name(cls, name: str) -> 'ToolConfig':
        path = get_package_path() / f'tools/{name}.json'
        if not os.path.exists(path): # TODO raise exceptions and handle message/exit in cli
            print(term_color(f'No known agentstack tool: {name}', 'red'))
            sys.exit(1)
        return cls.from_json(path)

    @classmethod
    def from_json(cls, path: Path) -> 'ToolConfig':
        data = open_json_file(path)
        try:
            return cls(**data)
        except pydantic.ValidationError as e:
            # TODO raise exceptions and handle message/exit in cli
            print(term_color(f"Error validating tool config JSON: \n{path}", 'red'))
            for error in e.errors():
                print(f"{' '.join(error['loc'])}: {error['msg']}")
            sys.exit(1)

    @property
    def module_name(self) -> str:
        return f"{self.name}_tool"

    def get_import_statement(self, framework: str) -> str:
        return f"from .{self.module_name} import {', '.join(self.tools)}"

    def get_impl_file_path(self, framework: str) -> Path:
        return get_package_path()/f'templates/{framework}/tools/{self.module_name}.py'

def get_all_tool_paths() -> list[Path]:
    paths = []
    tools_dir = get_package_path()/'tools'
    for file in tools_dir.iterdir():
        if file.is_file() and file.suffix == '.json':
            paths.append(file)
    return paths

def get_all_tool_names() -> list[str]:
    return [path.stem for path in get_all_tool_paths()]

def get_all_tools() -> list[ToolConfig]:
    return [ToolConfig.from_json(path) for path in get_all_tool_paths()]

