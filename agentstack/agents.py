from typing import Optional
import os
from pathlib import Path
import pydantic
from ruamel.yaml import YAML, YAMLError
from ruamel.yaml.scalarstring import FoldedScalarString
from agentstack import conf, log
from agentstack.exceptions import ValidationError
from agentstack.providers import parse_provider_model


AGENTS_FILENAME: Path = Path("src/config/agents.yaml")
AGENTS_PROMPT_TPL: str = "You are {role}. {backstory}\nYour personal goal is: {goal}"

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

    @property
    def provider(self) -> str:
        """The LLM provider ie. 'openai' or 'openrouter'"""
        return parse_provider_model(self.llm)[0]

    @property
    def model(self) -> str:
        """The model name ie. 'gpt-4o'"""
        return parse_provider_model(self.llm)[1]

    @property
    def prompt(self) -> str:
        """Concatenate the prompts for role, goal, and backstory."""
        return AGENTS_PROMPT_TPL.format(**{
            'role': self.role,
            'goal': self.goal,
            'backstory': self.backstory,
        })

    def model_dump(self, *args, **kwargs) -> dict:
        dump = super().model_dump(*args, **kwargs)
        dump.pop('name')  # name is the key, so keep it out of the data
        # format these as FoldedScalarStrings
        for key in ('role', 'goal', 'backstory'):
            dump[key] = FoldedScalarString(dump.get(key) or "")
        return {self.name: dump}

    def write(self):
        log.debug(f"Writing agent {self.name} to {AGENTS_FILENAME}")
        filename = conf.PATH / AGENTS_FILENAME

        with open(filename, 'r') as f:
            data = yaml.load(f) or {}

        data.update(self.model_dump())

        with open(filename, 'w') as f:
            yaml.dump(data, f)

    def __enter__(self) -> 'AgentConfig':
        return self

    def __exit__(self, *args):
        self.write()


def get_all_agent_names() -> list[str]:
    filename = conf.PATH / AGENTS_FILENAME
    if not os.path.exists(filename):
        log.debug(f"Project does not have an {AGENTS_FILENAME} file.")
        return []
    with open(filename, 'r') as f:
        data = yaml.load(f) or {}
    return list(data.keys())


def get_all_agents() -> list[AgentConfig]:
    return [AgentConfig(name) for name in get_all_agent_names()]


def get_agent(name: str) -> Optional[AgentConfig]:
    """Get an agent configuration by name."""
    return AgentConfig(name)

