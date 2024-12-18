from typing import Optional, Protocol, runtime_checkable
from types import ModuleType
import os
import sys
from pathlib import Path
from importlib import import_module
import pydantic
from agentstack.exceptions import ValidationError
from agentstack.utils import get_package_path, open_json_file, term_color, snake_to_camel


class ToolConfig(pydantic.BaseModel):
    """
    This represents the configuration data for a tool.
    It parses and validates the `config.json` file and provides a dynamic 
    interface for interacting with the tool implementation.
    """

    name: str
    category: str
    tools: list[str]
    url: Optional[str] = None
    cta: Optional[str] = None
    env: Optional[dict] = None
    dependencies: Optional[list[str]] = None
    post_install: Optional[str] = None
    post_remove: Optional[str] = None

    @classmethod
    def from_tool_name(cls, name: str) -> 'ToolConfig':
        path = get_package_path() / f'tools/{name}/config.json'
        if not os.path.exists(path):  # TODO raise exceptions and handle message/exit in cli
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
                print(f"{' '.join([str(loc) for loc in error['loc']])}: {error['msg']}")
            sys.exit(1)

    @property
    def type(self) -> type:
        """
        Dynamically generate a type for the tool module.
        ie. indicate what methods it's importable module should have.
        """
        def method_stub(name: str):
            def not_implemented(*args, **kwargs):
                raise NotImplementedError((
                    f"Method '{name}' is configured in config.json for tool '{self.name}'"
                    f"but has not been implemented in the tool module ({self.module_name})."
                ))
            return not_implemented

        type_ = type(f'{snake_to_camel(self.name)}Module', (Protocol,), {  # type: ignore[arg-type]
            method_name: method_stub(method_name) for method_name in self.tools
        })
        return runtime_checkable(type_)

    @property
    def module_name(self) -> str:
        """Module name for the tool module."""
        return f"agentstack.tools.{self.name}"

    @property
    def module(self) -> ModuleType:
        """
        Import the tool module and validate that it implements the required methods.
        Returns the imported module ready for direct use.
        """
        try:
            _module = import_module(self.module_name)
            assert isinstance(_module, self.type)
            return _module
        except AssertionError as e:
            raise ValidationError((
                f"Tool module `{self.module_name}` does not match the expected implementation. \n"
                f"The tool's config.json file lists the following public methods: `{'`, `'.join(self.tools)}` "
                f"but only implements: '{'`, `'.join([m for m in dir(_module) if not m.startswith('_')])}`"
            ))
        except ModuleNotFoundError as e:
            raise ValidationError((
                f"Could not import tool module: {self.module_name}\n"
                f"Are you sure you have installed the tool? (agentstack tools add {self.name})\n"
                f"ModuleNotFoundError: {e}"
            ))


def get_all_tool_paths() -> list[Path]:
    """
    Get all the paths to the tool configuration files.
    ie. agentstack/tools/<tool_name>/
    Tools are identified by having a `config.json` file instide the tools/<tool_name> directory.
    """
    paths = []
    tools_dir = get_package_path() / 'tools'
    for tool_dir in tools_dir.iterdir():
        if tool_dir.is_dir():
            config_path = tool_dir / 'config.json'
            if config_path.exists():
                paths.append(tool_dir)
    return paths


def get_all_tool_names() -> list[str]:
    return [path.stem for path in get_all_tool_paths()]


def get_all_tools() -> list[ToolConfig]:
    return [ToolConfig.from_tool_name(path) for path in get_all_tool_names()]
