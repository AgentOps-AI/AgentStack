from typing import Optional, Union
import os
import json
from pathlib import Path
from pydantic import BaseModel


DEFAULT_FRAMEWORK = "crewai"
CONFIG_FILENAME = "agentstack.json"
ENV_FILEMANE = ".env"

class ConfigFile(BaseModel):
    """
    Interface for interacting with the agentstack.json file inside a project directory.
    Handles both data validation and file I/O.
    
    `path` is the directory where the agentstack.json file is located. Defaults
    to the current working directory.
    
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
    """
    framework: Optional[str] = DEFAULT_FRAMEWORK
    tools: list[str] = []
    telemetry_opt_out: Optional[bool] = None
    default_model: Optional[str] = None
    
    def __init__(self, path: Union[str, Path, None] = None):
        path = Path(path) if path else Path.cwd()
        if os.path.exists(path / CONFIG_FILENAME):
            with open(path / CONFIG_FILENAME, 'r') as f:
                super().__init__(**json.loads(f.read()))
        else:
            raise FileNotFoundError(f"File {path / CONFIG_FILENAME} does not exist.")
        self._path = path # attribute needs to be set after init

    def model_dump(self, *args, **kwargs) -> dict:
        # Ignore None values
        dump = super().model_dump(*args, **kwargs)
        return {key: value for key, value in dump.items() if value is not None}
    
    def write(self):
        with open(self._path / CONFIG_FILENAME, 'w') as f:
            f.write(json.dumps(self.model_dump(), indent=4))
    
    def __enter__(self) -> 'ConfigFile': return self
    def __exit__(self, *args): self.write()


class EnvFile:
    """
    Interface for interacting with the .env file inside a project directory.
    Unlike the ConfigFile, we do not re-write the entire file on every change, 
    and instead just append new lines to the end of the file. This preseres
    comments and other formatting that the user may have added and prevents
    opportunities for data loss.
    
    `path` is the directory where the .env file is located. Defaults to the
    current working directory.
    `filename` is the name of the .env file, defaults to '.env'.
    
    Use it as a context manager to make and save edits:
    ```python
    with EnvFile() as env:
        env.append_if_new('ENV_VAR', 'value')
    ```
    """
    variables: dict[str, str]
    
    def __init__(self, path: Union[str, Path, None] = None, filename: str = ENV_FILEMANE):
        self._path = Path(path) if path else Path.cwd()
        self._filename = filename
        self.read()
    
    def __getitem__(self, key):
        return self.variables[key]

    def __setitem__(self, key, value):
        if key in self.variables:
            raise ValueError("EnvFile does not allow overwriting values.")
        self.append_if_new(key, value)
    
    def __contains__(self, key) -> bool:
        return key in self.variables
    
    def append_if_new(self, key, value):
        if not key in self.variables:
            self.variables[key] = value
            self._new_variables[key] = value
    
    def read(self):
        def parse_line(line):
            key, value = line.split('=')
            return key.strip(), value.strip()

        if os.path.exists(self._path / self._filename):
            with open(self._path / self._filename, 'r') as f:
                self.variables = dict([parse_line(line) for line in f.readlines() if '=' in line])
        else:
            self.variables = {}
        self._new_variables = {}
    
    def write(self):
        with open(self._path / self._filename, 'a') as f:
            for key, value in self._new_variables.items():
                f.write(f"\n{key}={value}")
    
    def __enter__(self) -> 'EnvFile': return self
    def __exit__(self, *args): self.write()

