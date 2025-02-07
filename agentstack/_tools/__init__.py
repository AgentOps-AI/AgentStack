from typing import Optional, Any, Callable, Protocol, runtime_checkable
from types import ModuleType
import enum
import os
import sys
from pathlib import Path
from importlib import import_module
import pydantic
from ruamel.yaml import YAML, YAMLError
from agentstack.exceptions import ValidationError
from agentstack.utils import get_package_path, open_json_file, snake_to_camel


TOOLS_DIR: Path = get_package_path() / '_tools'  # NOTE: if you change this dir, also update MANIFEST.in
TOOLS_CONFIG_FILENAME: str = 'config.json'
USER_TOOL_CONFIG_FILENAME: Path = Path('src/config/tools.yaml')

yaml = YAML()
yaml.preserve_quotes = True  # Preserve quotes in existing data

"""
As a tool author, this should be as easy as possible to interact with:

``` # config.json
{
    "name": "my_tool",
    ...
    "tools": {
        "tool_function": {
            "actions": ["read", "write"],
            "allowed_dirs": ["/home/user/*"],
            "allowed_extensions": ["*.txt"]
        },
        ...
    }
}
```

``` # my_tool.py
def tool_function(vars_need_to_be_preserved_for_llms) -> str:
    permissions = tools.get_permissions(tool_function)
    ...
    
    if permissions.READ:
        ...
    if permissions.WRITE:
        ...
    if permissions.EXECUTE:
        ...

    permissions.allowed_dirs  # -> ['/home/user/*']
    permissions.allowed_extensions  # -> ['*.txt']
    ...
```

`allowed_dirs` and `allowed_extensions` are optional, and up to the tool integrator to implement, 
but in this case we're using patterns that are compatible with `fnmatch`.

As a project user, this should be as easy as possible to interact with.
They should be able to inherit sane defaults from the tool author. 
In order to explicitly include a function in the tools available to the user's agent
we do need the function to be listed in the config file. It would be nice if we
didn't have to list all of the permissions, however. Although, that would be an
easy way to allow them to override defaults. 

``` # src/config/tools.yaml
my_tool:
    other_tool_function: ~  # (or empty) inherit defaults
    tool_function:
        actions: ['read', 'write']
        allowed_dirs: ['/home/user/*']
        allowed_extensions: ['*.txt']
```

TODO How do we determine which agent is using the tools? Maybe we leave out agent-specific
configuration for tools for now and just have them at the application level?
``` # src/stack.py
...
@agentstack.agent
def get_agent() -> Agent:
    return Agent(
        tools=[*agentstack.tools['my_tool'], ]
    )
"""


class Action(enum.Enum):
    READ = 'read'
    WRITE = 'write'
    EXECUTE = 'execute'


class ToolPermission(pydantic.BaseModel):
    """
    Control which features of a tool are available to an agent.

    This solves a few problems:
    - Some tools expose a number of functions, which may overwhelm the context of an agent.
    - Some tools interact with the system they are running on, and should be restricted to
    specific directories, or specific operations.
    - Some tools allow execution of code and should be restricted to specific features.

    Considerations:
    - Users and the CLI will have to interact with this configuration format and it should be
    easy to understand.
    - Tools may need additional configuration to define what features are available.

    TODO
    - Tool configurations should be specific to an agent, not the whole project.
    - Do we need to support modification of these rules via the CLI?
    """

    tool_name: str
    function_name: str
    tool_config: 'ToolConfig'
    _actions: list[Action]
    _attributes: dict[str, Any]

    def __init__(self, tool_name: str, function_name: str):
        self.tool_name = tool_name
        self.function_name = function_name
        self.tool_config = ToolConfig.from_tool_name(self.tool_name)

        try:
            config = self.tool_config.tools[self.function_name]
            self._actions = config.pop('actions', [])
            self._attributes = config
        except KeyError:
            raise ValidationError(f"Function '{self.function_name}' not found in tool '{self.tool_name}'")

        # TODO we have loaded the default tool config for the actions, now we need to overlay the user's preferences.

    @property
    def READ(self) -> bool:
        return Action.READ in self._actions

    @property
    def WRITE(self) -> bool:
        return Action.WRITE in self._actions

    @property
    def EXECUTE(self) -> bool:
        return Action.EXECUTE in self._actions

    def __getattr__(self, item):
        """
        Allow access to other variables defined in the tool config.
        If the variable is not defined, return None.
        """
        if item in self._attributes:
            return self._attributes[item]
        return None


class ToolConfig(pydantic.BaseModel):
    """
    This represents the configuration data for a tool.
    It parses and validates the `config.json` file and provides a dynamic
    interface for interacting with the tool implementation.
    """

    name: str
    category: str
    tools: dict[str, Any]
    url: Optional[str] = None
    cta: Optional[str] = None
    env: Optional[dict] = None
    dependencies: Optional[list[str]] = None
    post_install: Optional[str] = None
    post_remove: Optional[str] = None

    @pydantic.validator('tools')
    def validate_tools(cls, value):
        """
        Validate that each tool is a dict and has an 'actions' key which lists 'read', 'write', and/or 'execute'.
        """
        for tool in value:
            if not isinstance(tool, dict):
                raise pydantic.ValidationError(f"tools.{tool} is not a dict.")
            if 'actions' not in tool:
                raise pydantic.ValidationError(f"tools.{tool} does not have a key: 'actions'.")
            if not isinstance(tool['actions'], list):
                raise pydantic.ValidationError(f"tools.{tool}.actions is not a list.")
            for action in tool['actions']:
                if action not in Action.__members__.values():
                    raise pydantic.ValidationError(f"tools.{tool} has an invalid action: {action}.")
        return value

    @classmethod
    def from_tool_name(cls, name: str) -> 'ToolConfig':
        path = TOOLS_DIR / name / TOOLS_CONFIG_FILENAME
        if not os.path.exists(path):
            raise ValidationError(f'No known agentstack tool: {name}')
        return cls.from_json(path)

    @classmethod
    def from_json(cls, path: Path) -> 'ToolConfig':
        data = open_json_file(path)
        try:
            return cls(**data)
        except pydantic.ValidationError as e:
            error_str = "Error validating tool config:\n"
            for error in e.errors():
                error_str += f"{' '.join([str(loc) for loc in error['loc']])}: {error['msg']}\n"
            raise ValidationError(f"Error loading tool from {path}.\n{error_str}")

    @property
    def tool_names(self) -> list[str]:
        return list(self.tools.keys())

    @property
    def type(self) -> type:
        """
        Dynamically generate a type for the tool module.
        ie. indicate what methods it's importable module should have.
        """

        def method_stub(name: str):
            def not_implemented(*args, **kwargs):
                raise NotImplementedError(
                    f"Method '{name}' is configured in config.json for tool '{self.name}'"
                    f"but has not been implemented in the tool module ({self.module_name})."
                )

            return not_implemented

        # fmt: off
        type_ = type(f'{snake_to_camel(self.name)}Module', (Protocol,), {  # type: ignore[arg-type]
            method_name: method_stub(method_name) for method_name in self.tool_names
        },)
        # fmt: on
        return runtime_checkable(type_)

    @property
    def module_name(self) -> str:
        """Module name for the tool module."""
        return f"agentstack._tools.{self.name}"

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
            raise ValidationError(
                f"Tool module `{self.module_name}` does not match the expected implementation. \n"
                f"The tool's config.json file lists the following public methods: `{'`, `'.join(self.tool_names)}` "
                f"but only implements: '{'`, `'.join([m for m in dir(_module) if not m.startswith('_')])}`"
            )
        except ModuleNotFoundError as e:
            raise ValidationError(
                f"Could not import tool module: {self.module_name}\n"
                f"Are you sure you have installed the tool? (agentstack tools add {self.name})\n"
                f"ModuleNotFoundError: {e}"
            )


class UserToolConfig(pydantic.BaseModel):
    """
    Interface for reading a user's tool configuration from a project. 

    Config Schema
    -------------
    name: str
        The name of the agent; used for lookup.
    role: str
        The role of the agent.
    goal: str
        The goal of the agent.
    backstory: str
        The backstory of the agent.
    llm: str
        The model this agent should use.
        Adheres to the format set by the framework.
    """

    name: str
    role: str = ""
    goal: str = ""
    backstory: str = ""
    llm: str = ""

    def __init__(self, name: str):
        filename = conf.PATH / AGENTS_FILENAME

        try:
            with open(filename, 'r') as f:
                data = yaml.load(f) or {}
            data = data.get(name, {}) or {}
            super().__init__(**{**{'name': name}, **data})
        except YAMLError as e:
            # TODO format MarkedYAMLError lines/messages
            raise ValidationError(f"Error parsing agents file: {filename}\n{e}")
        except pydantic.ValidationError as e:
            error_str = "Error validating tool config:\n"
            for error in e.errors():
                error_str += f"{' '.join([str(loc) for loc in error['loc']])}: {error['msg']}\n"
            raise ValidationError(f"Error loading tool {name} from {filename}.\n{error_str}")


def get_permissions(func: Callable) -> ToolPermission:
    """
    Get the permissions for a tool function.
    We derive the tool name and function name from the function's module and name.
    """
    return ToolPermission(
        tool_name=function.__module__.split('.')[-1],
        function_name=function.__name__,
    )


def get_all_tool_paths() -> list[Path]:
    """
    Get all the paths to the tool configuration files.
    ie. agentstack/_tools/<tool_name>/
    Tools are identified by having a `config.json` file inside the _tools/<tool_name> directory.
    """
    paths = []
    for tool_dir in TOOLS_DIR.iterdir():
        if tool_dir.is_dir():
            config_path = tool_dir / TOOLS_CONFIG_FILENAME
            if config_path.exists():
                paths.append(tool_dir)
    return paths


def get_all_tool_names() -> list[str]:
    return [path.stem for path in get_all_tool_paths()]


# TODO tool configs don't get modified at runtime, so we can safely cache them.
def get_all_tools() -> list[ToolConfig]:
    return [ToolConfig.from_tool_name(path) for path in get_all_tool_names()]
