from typing import Optional, Callable, Protocol, runtime_checkable
from types import ModuleType
import enum
import os
import sys
from pathlib import Path
from importlib import import_module
import pydantic
from agentstack.exceptions import ValidationError
from agentstack.utils import get_package_path, open_json_file, snake_to_camel


TOOLS_DIR: Path = get_package_path() / '_tools'  # NOTE: if you change this dir, also update MANIFEST.in
TOOLS_CONFIG_FILENAME: str = 'config.json'


class Action(enum.Enum):
    READ = 'read'
    WRITE = 'write'
    EXECUTE = 'execute'


def performs_actions(*actions: str) -> Callable:
    """
    Decorator to note the Actions a tool exposes. 
    
    Use inside of a tool implementation to indicate which actions the function performs.
    
    ```
    from agentstack import tools
    
    @tools.performs_actions('read', 'write')
    def my_tool_function(key: str, value: str):
        ...
    ```

    I also wonder about passing more configuration information to a tools in a semi-standardized way:
    ```
    @tools.performs_read(allowed_dirs=['/home/user/*'], allowed_extensions=['*.txt'])
    def my_tool_function(key: str, value: str, **kwargs):
        allowed_dirs = kwargs.get('allowed_dirs', ['/'])
        allowed_extensions = kwargs.get('allowed_extensions', ['*.*'])
        # it will always be up to the integrator to actually enforce these rules
        ...
    
    ALLOWED_SH_COMMANDS = ['ls', 'cat', ...]
    
    @tools.performs_exec(language='sh', allowed_commands=ALLOWED_SH_COMMANDS)
    def my_tool_function(key: str, value: str, **kwargs):
        ...
    ```
    
    Later, the user needs to be able to override all of these rules in their project. 
    - Remember, each agent can have different rules.
        - Would be great if this could inherit from a shared base.
    
    # project/src/config/tools.yaml
    defaults:
        tool_name:
            function_name: &tool_name__function_name
                read:
                    allowed_dirs: ['/home/user/*']
                    allowed_extensions: ['*.txt']
                write:
                    allowed_dirs: ['/home/user/*']
                    allowed_extensions: ['*.txt']
    agent_name:
        tool_name: 
            function_name: << *tool_name__function_name
    ...
    
    I don't love that...
    """

    try:
        _actions: list[Action] = []
        for action_name in actions:
            _actions.append(Action(action_name))
    except ValueError as e:
        raise ValidationError(f"Invalid action name '{action_name}' passed to `tools.performs_actions`")
    
    def decorator(func):
        func.__tool_actions = _actions
        return func

    return decorator


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
    - Determine where and how we want to store this data. (conf/tools.yaml in the user's project?)
    - Tool configurations should be specific to an agent, not the whole project. 
    - If we do implement read/write/execute rules we need some way to mark tool functions as being relevant.
    - Do we write a config file to the users project that lists all permissions as allowed by default and
      instruct users to modify it?
    - Do we need to support modification of these rules via the CLI?
    """


    function_name: str
    action: Action


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
            method_name: method_stub(method_name) for method_name in self.tools
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
                f"The tool's config.json file lists the following public methods: `{'`, `'.join(self.tools)}` "
                f"but only implements: '{'`, `'.join([m for m in dir(_module) if not m.startswith('_')])}`"
            )
        except ModuleNotFoundError as e:
            raise ValidationError(
                f"Could not import tool module: {self.module_name}\n"
                f"Are you sure you have installed the tool? (agentstack tools add {self.name})\n"
                f"ModuleNotFoundError: {e}"
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


def get_all_tools() -> list[ToolConfig]:
    return [ToolConfig.from_tool_name(path) for path in get_all_tool_names()]
