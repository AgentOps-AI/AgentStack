from typing import Optional
import os
from pathlib import Path
import pydantic
from ruamel.yaml import YAML, YAMLError
from ruamel.yaml.scalarstring import FoldedScalarString
from agentstack import conf, log
from agentstack.exceptions import ValidationError


TASKS_FILENAME: Path = Path("src/config/tasks.yaml")
TASKS_PROMPT_TPL: str = ("\nThis is the expect criteria for your final answer: {expected_output}\n "
    "you MUST return the actual complete content as the final answer, not a summary. "
    "\nCurrent Task: {description}\n\nBegin! This is VERY important to you, use the "
    "tools available and give your best Final Answer, your job depends on it!\n\nThought:")

yaml = YAML()
yaml.preserve_quotes = True  # Preserve quotes in existing data


class TaskConfig(pydantic.BaseModel):
    """
    Interface for interacting with a task configuration.

    Multiple tasks are stored in a single YAML file, so we always look up the
    requested task by `name`.

    Use it as a context manager to make and save edits:
    ```python
    with TaskConfig('task_name') as config:
        config.description = "foo"

    Config Schema
    -------------
    name: str
        The name of the agent; used for lookup.
    description: str
        The description of the task.
    expected_output: str
        The expected output of the task.
    agent: str
        The agent to use for the task.
    """

    name: str
    description: str = ""
    expected_output: str = ""
    agent: str = ""

    def __init__(self, name: str):
        filename = conf.PATH / TASKS_FILENAME
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
            raise ValidationError(f"Error parsing tasks file: {filename}\n{e}")
        except pydantic.ValidationError as e:
            error_str = "Error validating tasks config:\n"
            for error in e.errors():
                error_str += f"{' '.join([str(loc) for loc in error['loc']])}: {error['msg']}\n"
            raise ValidationError(f"Error loading task {name} from {filename}.\n{error_str}")

    @property
    def prompt(self) -> str:
        """Format a complete prompt which includes the task description and expected output."""
        return TASKS_PROMPT_TPL.format(**{
            'description': self.description,
            'expected_output': self.expected_output,
        })

    def model_dump(self, *args, **kwargs) -> dict:
        dump = super().model_dump(*args, **kwargs)
        dump.pop('name')  # name is the key, so keep it out of the data
        # format these as FoldedScalarStrings
        for key in ('description', 'expected_output', 'agent'):
            dump[key] = FoldedScalarString(dump.get(key) or "")
        return {self.name: dump}

    def write(self):
        log.debug(f"Writing task {self.name} to {TASKS_FILENAME}")
        filename = conf.PATH / TASKS_FILENAME

        with open(filename, 'r') as f:
            data = yaml.load(f) or {}

        data.update(self.model_dump())

        with open(filename, 'w') as f:
            yaml.dump(data, f)

    def __enter__(self) -> 'TaskConfig':
        return self

    def __exit__(self, *args):
        self.write()


def get_all_task_names() -> list[str]:
    filename = conf.PATH / TASKS_FILENAME
    if not os.path.exists(filename):
        log.debug(f"Project does not have an {TASKS_FILENAME} file.")
        return []
    with open(filename, 'r') as f:
        data = yaml.load(f) or {}
    return list(data.keys())


def get_all_tasks() -> list[TaskConfig]:
    return [TaskConfig(name) for name in get_all_task_names()]


def get_task(name: str) -> TaskConfig:
    """Get a task configuration by name."""
    return TaskConfig(name)

