from typing import Optional, Union
import os
import json
from pathlib import Path
from pydantic import BaseModel
from agentstack.utils import get_version


DEFAULT_FRAMEWORK = "crewai"
CONFIG_FILENAME = "agentstack.json"

DEBUG: bool = False

# The path to the project directory ie. working directory.
PATH: Path = Path()


class NoProjectError(Exception):
    pass


def assert_project() -> None:
    try:
        ConfigFile()
        return
    except FileNotFoundError:
        raise NoProjectError("Could not find agentstack.json, are you in an AgentStack project directory?")


def set_path(path: Union[str, Path, None]):
    """Set the path to the project directory."""
    global PATH
    PATH = Path(path) if path else Path()


def set_debug(debug: bool):
    """
    Set the debug flag in the project's configuration for the session; does not
    get saved to the project's configuration file.
    """
    global DEBUG
    DEBUG = debug


def get_framework() -> Optional[str]:
    """The framework used in the project. Will be available after PATH has been set
    and if we are inside a project directory.
    """
    try:
        return ConfigFile().framework
    except FileNotFoundError:
        return None  # not in a project directory; that's okay


def get_installed_tools() -> list[str]:
    """The tools used in the project. Will be available after PATH has been set
    and if we are inside a project directory.
    """
    try:
        return ConfigFile().tools
    except FileNotFoundError:
        return []


class ConfigFile(BaseModel):
    """
    Interface for interacting with the agentstack.json file inside a project directory.
    Handles both data validation and file I/O.

    Use it as a context manager to make and save edits:
    ```python
    with ConfigFile() as config:
        config.tools.append('tool_name')
    ```

    Config Schema
    -------------
    framework: str
        The framework used in the project. Defaults to 'crewai'.
    tools: list[str]
        A list of tools that are currently installed in the project.
    telemetry_opt_out: Optional[bool]
        Whether the user has opted out of telemetry.
    default_model: Optional[str]
        The default model to use when generating agent configurations.
    agentstack_version: Optional[str]
        The version of agentstack used to generate the project.
    template: Optional[str]
        The template used to generate the project.
    template_version: Optional[str]
        The version of the template system used to generate the project.
    use_git: Optional[bool]
        Whether to use git for automatic commits of you project.
    """

    framework: str = DEFAULT_FRAMEWORK  # TODO this should probably default to None
    tools: list[str] = []
    telemetry_opt_out: Optional[bool] = None
    default_model: Optional[str] = None
    agentstack_version: Optional[str] = get_version()
    template: Optional[str] = None
    template_version: Optional[str] = None
    use_git: Optional[bool] = True

    def __init__(self):
        if os.path.exists(PATH / CONFIG_FILENAME):
            with open(PATH / CONFIG_FILENAME, 'r') as f:
                super().__init__(**json.loads(f.read()))
        else:
            raise FileNotFoundError(f"File {PATH / CONFIG_FILENAME} does not exist.")

    def model_dump(self, *args, **kwargs) -> dict:
        # Ignore None values
        dump = super().model_dump(*args, **kwargs)
        return {key: value for key, value in dump.items() if value is not None}

    def write(self):
        with open(PATH / CONFIG_FILENAME, 'w') as f:
            f.write(json.dumps(self.model_dump(), indent=4))

    def __enter__(self) -> 'ConfigFile':
        return self

    def __exit__(self, *args):
        self.write()
