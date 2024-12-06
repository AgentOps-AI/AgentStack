from typing import Optional
import os
from pathlib import Path
import pydantic
from ruamel.yaml import YAML, YAMLError
from ruamel.yaml.scalarstring import FoldedScalarString
from agentstack import ValidationError


AGENTS_FILENAME: Path = Path("src/config/agents.yaml")

yaml = YAML()
yaml.preserve_quotes = True  # Preserve quotes in existing data


class AgentConfig(pydantic.BaseModel):
    """
    Interface for interacting with an agent configuration.

    Multiple agents are stored in a single YAML file, so we always look up the
    requested agent by `name`.

    Use it as a context manager to make and save edits:
    ```python
    with AgentConfig('agent_name') as config:
        config.llm = "openai/gpt-4o"

    Config Schema
    -------------
    name: str
        The name of the agent; used for lookup.
    role: Optional[str]
        The role of the agent.
    goal: Optional[str]
        The goal of the agent.
    backstory: Optional[str]
        The backstory of the agent.
    llm: Optional[str]
        The model this agent should use.
        Adheres to the format set by the framework.
    """

    name: str
    role: Optional[str] = ""
    goal: Optional[str] = ""
    backstory: Optional[str] = ""
    llm: Optional[str] = ""

    def __init__(self, name: str, path: Optional[Path] = None):
        if not path:
            path = Path()

        filename = path / AGENTS_FILENAME
        if not os.path.exists(filename):
            os.makedirs(filename.parent, exist_ok=True)
            filename.touch()

        try:
            with open(filename, 'r') as f:
                data = yaml.load(f) or {}
            data = data.get(name, {}) or {}
            super().__init__(**{**{'name': name}, **data})
        except YAMLError as e:
            # TODO format MarkedYAMLError lines/messages
            raise ValidationError(f"Error parsing agents file: {filename}\n{e}")
        except pydantic.ValidationError as e:
            error_str = "Error validating agent config:\n"
            for error in e.errors():
                error_str += f"{' '.join([str(loc) for loc in error['loc']])}: {error['msg']}\n"
            raise ValidationError(f"Error loading agent {name} from {filename}.\n{error_str}")

        # store the path *after* loading data
        self._path = path

    def model_dump(self, *args, **kwargs) -> dict:
        dump = super().model_dump(*args, **kwargs)
        dump.pop('name')  # name is the key, so keep it out of the data
        # format these as FoldedScalarStrings
        for key in ('role', 'goal', 'backstory'):
            dump[key] = FoldedScalarString(dump.get(key) or "")
        return {self.name: dump}

    def write(self):
        filename = self._path / AGENTS_FILENAME

        with open(filename, 'r') as f:
            data = yaml.load(f) or {}

        data.update(self.model_dump())

        with open(filename, 'w') as f:
            yaml.dump(data, f)

    def __enter__(self) -> 'AgentConfig':
        return self

    def __exit__(self, *args):
        self.write()
