from typing import Optional, Union
import string
import os, sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib
from agentstack import conf


ENV_FILEMANE = ".env"
PYPROJECT_FILENAME = "pyproject.toml"


class EnvFile:
    """
    Interface for interacting with the .env file inside a project directory.
    Unlike the ConfigFile, we do not re-write the entire file on every change,
    and instead just append new lines to the end of the file. This preseres
    comments and other formatting that the user may have added and prevents
    opportunities for data loss.

    If the value of a variable is None, it will be commented out when it is written
    to the file. This gives the user a suggestion, but doesn't override values that
    may have been set by the user via other means.

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

    def __init__(self, filename: str = ENV_FILEMANE):
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
        if key not in self.variables:
            self.variables[key] = value
            self._new_variables[key] = value

    def read(self):
        def parse_line(line):
            key, value = line.split('=')
            return key.strip(string.whitespace + '#'), value.strip(string.whitespace + '"')

        if os.path.exists(conf.PATH / self._filename):
            with open(conf.PATH / self._filename, 'r') as f:
                self.variables = dict([parse_line(line) for line in f.readlines() if '=' in line])
        else:
            self.variables = {}
        self._new_variables = {}

    def write(self):
        with open(conf.PATH / self._filename, 'a') as f:
            for key, value in self._new_variables.items():
                if value is None:
                    f.write(f'\n#{key}=""')  # comment-out empty values
                else:
                    f.write(f'\n{key}={value}')

    def __enter__(self) -> 'EnvFile':
        return self

    def __exit__(self, *args):
        self.write()


class ProjectFile:
    """
    Interface for interacting with pyproject.toml files inside of a project directory.
    This class is read-only and does not support writing changes back to the file.
    We expose project metadata as properties to support migration to other formats
    in the future.
    """

    _data: dict

    def __init__(self, filename: str = PYPROJECT_FILENAME):
        self._filename = filename
        self.read()

    @property
    def project_metadata(self) -> dict:
        try:
            return self._data['tool']['poetry']
        except KeyError:
            raise KeyError("No poetry metadata found in pyproject.toml.")

    @property
    def project_name(self) -> str:
        return self.project_metadata.get('name', '')

    @property
    def project_version(self) -> str:
        return self.project_metadata.get('version', '')

    @property
    def project_description(self) -> str:
        return self.project_metadata.get('description', '')

    def read(self):
        if os.path.exists(conf.PATH / self._filename):
            with open(conf.PATH / self._filename, 'rb') as f:
                self._data = tomllib.load(f)
        else:
            raise FileNotFoundError(f"File {conf.PATH / self._filename} does not exist.")
