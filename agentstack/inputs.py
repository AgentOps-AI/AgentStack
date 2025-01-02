from typing import Optional
import os
from pathlib import Path
from ruamel.yaml import YAML, YAMLError
from ruamel.yaml.scalarstring import FoldedScalarString
from agentstack import conf, log
from agentstack.exceptions import ValidationError


INPUTS_FILENAME: Path = Path("src/config/inputs.yaml")

yaml = YAML()
yaml.preserve_quotes = True  # Preserve quotes in existing data

# run_inputs are set at the beginning of the run and are not saved
run_inputs: dict[str, str] = {}


class InputsConfig:
    """
    Interface for interacting with inputs configuration.

    Use it as a context manager to make and save edits:
    ```python
    with InputsConfig() as inputs:
        inputs.topic = "Open Source Aritifical Intelligence"
    ```
    """

    _attributes: dict[str, str]

    def __init__(self):
        filename = conf.PATH / INPUTS_FILENAME

        if not os.path.exists(filename):
            os.makedirs(filename.parent, exist_ok=True)
            filename.touch()

        try:
            with open(filename, 'r') as f:
                self._attributes = yaml.load(f) or {}
        except YAMLError as e:
            # TODO format MarkedYAMLError lines/messages
            raise ValidationError(f"Error parsing inputs file: {filename}\n{e}")

    def __getitem__(self, key: str) -> str:
        return self._attributes[key]

    def __setitem__(self, key: str, value: str):
        self._attributes[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._attributes

    def to_dict(self) -> dict[str, str]:
        return self._attributes

    def model_dump(self) -> dict:
        dump = {}
        for key, value in self._attributes.items():
            dump[key] = FoldedScalarString(value)
        return dump

    def write(self):
        log.debug(f"Writing inputs to {INPUTS_FILENAME}")
        with open(conf.PATH / INPUTS_FILENAME, 'w') as f:
            yaml.dump(self.model_dump(), f)

    def __enter__(self) -> 'InputsConfig':
        return self

    def __exit__(self, *args):
        self.write()


def get_inputs() -> dict:
    """
    Get the inputs configuration file and override with run_inputs.
    """
    config = InputsConfig().to_dict()
    # run_inputs override saved inputs
    for key, value in run_inputs.items():
        config[key] = value
    return config


def add_input_for_run(key: str, value: str):
    """
    Add an input override for the current run.
    This is used by the CLI to allow inputs to be set at runtime.
    """
    run_inputs[key] = value
