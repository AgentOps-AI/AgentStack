from typing import Optional, Any, Callable, Protocol, runtime_checkable
from types import ModuleType
import os
from importlib import import_module
from functools import lru_cache
from pathlib import Path
import enum
import pydantic
from agentstack import conf, log
from agentstack.exceptions import ValidationError
from agentstack.utils import get_package_path, open_json_file, snake_to_camel
from agentstack import yaml


TOOLS_DIR: Path = get_package_path() / '_tools'  # NOTE: if you change this dir, also update MANIFEST.in
TOOLS_CONFIG_FILENAME: str = 'config.json'
USER_TOOL_CONFIG_FILENAME: str = 'src/config/tools.yaml'


def _get_user_tool_config_path() -> Path:
    return conf.PATH / USER_TOOL_CONFIG_FILENAME


def _get_custom_tool_path(name: str) -> Path:
    """Get the path to a custom tool."""
    return conf.PATH / 'src/tools' / name / TOOLS_CONFIG_FILENAME


def _get_builtin_tool_path(name: str) -> Path:
    """Get the path to a builtin tool."""
    return TOOLS_DIR / name / TOOLS_CONFIG_FILENAME


"""
Tool Authors
------------
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

Permissions passed to the tool take info account the developer-defined defaults 
and the preferences the user has overlaid on top of them.

If a user has not overridden prefs, the tool will get a base set of permissions, 
but the user's project will not have access to the function, so we're good. 

``` # my_tool.py
def tool_function() -> str:
    permissions = tools.get_permissions(tool_function)
    ...
    
    if permissions.READ:
        ...
    if permissions.WRITE:
        ...
    if permissions.EXECUTE:
        ...

    # extra permission are ad-hoc
    permissions.allowed_dirs  # -> ['/home/user/*']
    permissions.allowed_extensions  # -> ['*.txt']
    ...
```

`allowed_dirs` and `allowed_extensions` are optional, and up to the tool integrator to implement, 
but in this case we're using patterns that are compatible with `fnmatch`.

End Users
---------
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
    DELETE = 'delete'
    EXECUTE = 'execute'

    def __str__(self) -> str:
        return self.value


class ToolPermission(pydantic.BaseModel):
    """
    Indicate which permissions a tool has.

    This solves a few problems:
    - Some tools expose a number of functions, which may overwhelm the context of an agent.
    - Some tools interact with the system they are running on, and should be restricted to
      specific directories, or specific operations.
    - Some tools allow execution of code and should be restricted to specific features.

    Considerations:
    - Users and the CLI will have to interact with this configuration format and it should be
      easy to understand.
    - Tools may need additional configuration to define what features are available.

    This is used by both the tool's included configuration and the user's configuration
    to represent the permissions for a tool.

    TODO Tool configurations could be specific to an agent, not the whole project.
    This does make the configuration format that much more complex and the way we
    currently load tools into an agent does not have a marker for that.
    """

    actions: list[Action]
    attributes: dict[str, Any] = pydantic.Field(default_factory=dict)

    def __init__(self, **data):
        super().__init__(actions=data.pop('actions'), attributes=data)

    @property
    def READ(self) -> bool:
        """Is this tool allowed to read?"""
        return Action.READ in self.actions

    @property
    def WRITE(self) -> bool:
        """Is this tool allowed to write?"""
        return Action.WRITE in self.actions

    @property
    def DELETE(self) -> bool:
        """Is this tool allowed to delete?"""
        return Action.DELETE in self.actions

    @property
    def EXECUTE(self) -> bool:
        """Is this tool allowed to execute?"""
        return Action.EXECUTE in self.actions

    def __getattr__(self, name: str) -> Any:
        """Get an attribute from the attributes dict."""
        return self.attributes.get(name, None)

    @pydantic.model_serializer
    def ser_model(self) -> dict:
        """Merge attributes into top level"""
        return {**self.attributes, 'actions': self.actions}


class ToolConfig(pydantic.BaseModel):
    """
    This represents the configuration data for a tool.
    It parses and validates the `config.json` file and provides an interface for
    interacting with the tool implementation.
    User tool config data is incorporated to filter tools the user has allowed
    into their project along with any permissions they have set.
    """

    name: str
    category: str
    tools: dict[str, ToolPermission]
    url: Optional[str] = None
    cta: Optional[str] = None
    env: Optional[dict] = None
    dependencies: Optional[list[str]] = None
    post_install: Optional[str] = None
    post_remove: Optional[str] = None

    @classmethod
    def from_tool_name(cls, name: str) -> 'ToolConfig':
        # First check in the user's project directory for custom tools
        custom_path = _get_custom_tool_path(name)
        if custom_path.exists():
            return cls.from_json(custom_path)

        # Then check in the package's tools directory
        path = _get_builtin_tool_path(name)
        if not path.exists():
            raise ValidationError(f'No known agentstack tool: {name}')
        return cls.from_json(path)

    @classmethod
    def from_json(cls, path: Path) -> 'ToolConfig':
        """Load a tool's configuration from a path to a JSON file."""
        data = open_json_file(path)
        try:
            return cls(**data)
        except pydantic.ValidationError as e:
            error_str = "Error validating tool config:\n"
            for error in e.errors():
                error_str += f"{' '.join([str(loc) for loc in error['loc']])}: {error['msg']}\n"
            raise ValidationError(f"Error loading tool from {path}.\n{error_str}")

    def write_to_file(self, filename: Path):
        """Write the tool config to a json file."""
        if not filename.suffix == '.json':
            raise ValidationError(f"Filename must end with .json: {filename}")

        with open(filename, 'w') as f:
            f.write(self.model_dump_json(indent=4))

    @property
    def allowed_tools(self) -> dict[str, ToolPermission]:
        """Get the tools this project has access to."""
        try:
            user_config = UserToolConfig(self.name)
        except FileNotFoundError:
            log.debug(f"User has no tools.yaml file; allowing all tools.")
            return self.tools

        log.debug(
            f"Excluding tools from {self.name} based on project permissions: "
            f"{', '.join(self.tools.keys() - user_config.tools.keys()) or 'None'}\n"
            f"Modify this behavior in 'src/config/tools.yaml'."
        )

        filtered_perms = {}
        for func_name in user_config.tools:
            # TODO what about orphaned tools in the user config
            base_perms: Optional[ToolPermission] = self.tools.get(func_name)
            assert base_perms, f"Tool config.json for '{self.name}' does not include '{func_name}'."

            _user_perms: Optional[ToolPermission] = user_config.tools[func_name]
            if _user_perms is None:  # `None` if user chooses to inherit all defaults
                user_perms = {}
            if isinstance(_user_perms, ToolPermission):
                user_perms = _user_perms.model_dump()
            assert user_perms is not None, f"User tool permission got unexpected type {type(_user_perms)}."

            all_perms = {**base_perms.model_dump(), **user_perms}
            filtered_perms[func_name] = ToolPermission(**all_perms)
        return filtered_perms

    @property
    def tool_names(self) -> list[str]:
        """Get the names of all tools."""
        return list(self.tools.keys())

    @property
    def allowed_tool_names(self) -> list[str]:
        """Get the names of all tools this project has access to."""
        return list(self.allowed_tools.keys())

    @property
    def type(self) -> type:
        """
        Dynamically generate a type for the tool module.
        ie. indicate what methods it's importable module should have.
        """

        def method_stub(name: str):
            def not_implemented(*args, **kwargs):
                # this should never be called, but is here to indicate that the method
                # is not implemented in the tool module if for some reason it is called.
                raise NotImplementedError(  # pragma: no cover
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
        # Check if this is a custom tool in the user's project
        custom_path = _get_custom_tool_path(self.name)
        if custom_path.exists():
            return f"src.tools.{self.name}"

        # Otherwise, it's a package tool
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

    Usage:
    ```
    user_tool_config = UserToolConfig('tool_name')
    tool = user_tool_config.tools['tool_function']
    tool.actions # -> [Actions.READ, ...]
    tool.foobar # -> Any
    ```
    Use it as a context manager to make and save edits:
    ```python
    with UserToolConfig('tool_name') as config:
        # TODO `ToolPermission` might not be instantiated so this is a bad example
        config.tools['tool_function'].actions = [Actions.READ, Actions.WRITE]
    ```

    Or, just make a tool available to the user:
    ```python
    with UserToolConfig('tool_name') as config:
        config.add_tool(tool_config)
    ```

    Config Schema
    -------------
    name: str
        The name of the tool.
    tools: dict[str, Optional[ToolPermission]]
        A dictionary of tool names to permissions. Empty values inherit all from the tool's config.json.
    """

    name: str
    tools: dict[str, Optional[ToolPermission]] = pydantic.Field(default_factory=dict)

    def __init__(self, tool_name: str):
        filename = _get_user_tool_config_path()
        try:
            with open(filename, 'r') as f:
                data = yaml.parser.load(f) or {}
            data = data.get(tool_name, {}) or {}
            super().__init__(**{'name': tool_name, 'tools': data})
        except yaml.YAMLError as e:
            # TODO format MarkedYAMLError lines/messages
            raise ValidationError(f"Error parsing tools file: {filename}\n{e}")
        except pydantic.ValidationError as e:
            error_str = "Error validating user tool config:\n"
            for error in e.errors():
                error_str += f"{' '.join([str(loc) for loc in error['loc']])}: {error['msg']}\n"
            raise ValidationError(f"Error loading tool {tool_name} from {filename}.\n{error_str}")

    @classmethod
    def exists(cls) -> bool:
        """Check if a user tool config file exists."""
        return _get_user_tool_config_path().exists()

    @classmethod
    def initialize(cls) -> None:
        """
        Create a user tool config file if it does not exist and populate it with
        all of the tools available to the user. This is used to bring an existing
        project up to date with a UserToolConfig.
        """
        from agentstack.frameworks import get_templates_path

        framework = conf.get_framework()
        assert framework, "Not an agentstack project."
        template_path = get_templates_path(framework) / USER_TOOL_CONFIG_FILENAME
        filename = _get_user_tool_config_path()

        assert not filename.exists(), f"{filename} exists."
        with open(filename, 'w') as f:
            f.write(template_path.read_text())

        for tool_name in conf.get_installed_tools():
            tool_config = get_tool(tool_name)
            with cls(tool_name) as user_tool_config:
                user_tool_config.add_stubs()

    @property
    def tool_names(self) -> list[str]:
        """Get the names of all tools in the user config."""
        return list(self.tools.keys())

    def add_stubs(self) -> None:
        """
        Add stubs for all tools in the user config to the tool config file.
        This is used to bring an existing project up to date with a UserToolConfig.
        """
        tool_config = get_tool(self.name)
        self.tools = {key: None for key in tool_config.tool_names}

    def model_dump(self, *args, **kwargs) -> dict:
        model_dump = super().model_dump(*args, **kwargs)
        tool_name = model_dump.pop('name')  # `name` is the key, so keep it out of the data
        tool_data = model_dump.pop('tools')  # `tools` as a key is implied
        return {tool_name: tool_data}

    def write(self):
        filename = _get_user_tool_config_path()
        log.debug(f"Writing tool '{self.name}' to {filename}")

        with open(filename, 'r') as f:
            data = yaml.parser.load(f) or {}

        # update just this tool
        data.update(self.model_dump())

        with open(filename, 'w') as f:
            yaml.parser.dump(data, f)

    def __enter__(self) -> 'UserToolConfig':
        return self

    def __exit__(self, *args):
        self.write()


def get_permissions(func: Callable) -> ToolPermission:
    """
    Get the permissions for use inside of a tool function.
    We derive the tool name and function name from the function's module and name.
    This takes the user's preferences into account.
    """
    tool_name = func.__module__.split('.')[-1]
    func_name = func.__name__
    log.debug(f"Getting permissions for `{tool_name}.{func_name}`")
    return get_tool(tool_name).tools[func_name]


def get_tool(name: str) -> ToolConfig:
    """
    Get the tool configuration for a given tool name.
    """
    # TODO this is a candidate for caching
    return ToolConfig.from_tool_name(name)


@lru_cache()  # tool config paths do not change at runtime
def get_all_tool_paths() -> list[Path]:
    """
    Get all the paths to the tool configuration files.
    ie. agentstack/_tools/<tool_name>/
    Tools are identified by having a `config.json` file inside the _tools/<tool_name> directory.
    Also checks the user's project directory for custom tools.
    """
    paths = []

    # Get package tools
    for tool_dir in TOOLS_DIR.iterdir():
        if tool_dir.is_dir():
            config_path = tool_dir / TOOLS_CONFIG_FILENAME
            if config_path.exists():
                paths.append(tool_dir)

    # Get custom tools from user's project if in a project directory
    if conf.PATH:
        custom_tools_dir = conf.PATH / 'src/tools'
        if custom_tools_dir.exists():
            for tool_dir in custom_tools_dir.iterdir():
                if tool_dir.is_dir():
                    config_path = tool_dir / TOOLS_CONFIG_FILENAME
                    if config_path.exists():
                        paths.append(tool_dir)

    return paths


def get_all_tool_names() -> list[str]:
    """
    Get the names of all bundled tools.
    """
    return [path.stem for path in get_all_tool_paths()]


def get_all_tools() -> list[ToolConfig]:
    """
    Get configurations for all bundled tools.
    """
    return [get_tool(name) for name in get_all_tool_names()]
