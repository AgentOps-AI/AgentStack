from typing import Optional, Union
import re
import string
import os, sys
import string
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib
from agentstack import conf


ENV_FILENAME = ".env"
PYPROJECT_FILENAME = "pyproject.toml"


class EnvFile:
    """
    Interface for interacting with the .env file inside a project directory.
    Unlike the ConfigFile, we do not re-write the entire file on every change,
    and instead just append new lines to the end of the file. This preserves
    comments and other formatting that the user may have added and prevents
    opportunities for data loss.

    If the value of a variable is None, it will be commented out when it is written
    to the file. This gives the user a suggestion, but doesn't override values that
    may have been set by the user via other means (for example, but the user's shell).
    Commented variable are not re-parsed when the file is read.

    `path` is the directory where the .env file is located. Defaults to the
    current working directory.
    `filename` is the name of the .env file, defaults to '.env'.

    Use it as a context manager to make and save edits:
    ```python
    with EnvFile() as env:
        env.append_if_new('ENV_VAR', 'value')
    ```
    """

    # split the key-value pair on the first '=' character
    # allow spaces around the '=' character
    RE_PAIR = re.compile(r"^\s*([^\s=]+)\s*=\s*(.*)$")
    variables: dict[str, str]

    def __init__(self, filename: str = ENV_FILENAME):
        self._filename = filename
        self.read()

    def __getitem__(self, key) -> str:
        return self.variables[key]

    def __setitem__(self, key, value) -> None:
        if key in self.variables:
            raise ValueError("EnvFile does not allow overwriting values.")
        self.append_if_new(key, value)

    def __contains__(self, key) -> bool:
        return key in self.variables

    def append_if_new(self, key, value) -> None:
        """Setting a non-existent key will append it to the end of the file."""
        if key not in self.variables:
            self.variables[key] = value
            self._new_variables[key] = value

    def read(self) -> None:
        def parse_line(line) -> tuple[str, str]:
            """
            Parse a line from the .env file.
            Pairs are split on the first '=' character, and stripped of whitespace & quotes.
            Only the last occurrence of a variable is stored.
            """
            match = self.RE_PAIR.match(line)
            
            if not match:
                raise ValueError(f"Invalid line in .env file: {line}")
            
            key, value = match.groups()
            return key, value.strip(' "')

        if os.path.exists(conf.PATH / self._filename):
            with open(conf.PATH / self._filename, 'r') as f:
                self.variables = dict(
                    [parse_line(line) for line in f.readlines() if '=' in line and not line.startswith('#')]
                )
        else:
            self.variables = {}
        self._new_variables = {}

    def write(self) -> None:
        """Append new variables to the end of the file."""
        with open(conf.PATH / self._filename, 'a') as f:
            for key, value in self._new_variables.items():
                if value is None:
                    f.write(f'\n#{key}=""')  # comment-out empty values
                else:
                    f.write(f'\n{key}={value}')

    def __enter__(self) -> 'EnvFile':
        return self

    def __exit__(self, *args) -> None:
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
        """
        [project]
        name = "project_name"
        version = "0.0.1"
        description = "foo bar"
        authors = [
            { name = "Name <Email>" }
        ]
        license = { text = "MIT" }
        requires-python = ">=3.10"

        dependencies = [
            ...
        ]
        """
        try:
            return self._data['project']
        except KeyError:
            raise KeyError("No project metadata found in pyproject.toml.")

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
