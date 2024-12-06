from typing import Optional
import os, sys
from pathlib import Path
import pydantic
from ruamel.yaml import YAML, YAMLError
from ruamel.yaml.scalarstring import FoldedScalarString
from agentstack import ValidationError


TASKS_FILENAME: Path = Path("src/config/tasks.yaml")

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
    description: Optional[str]
        The description of the task.
    expected_output: Optional[str]
        The expected output of the task.
    agent: Optional[str]
        The agent to use for the task.
    """
    name: str
    description: Optional[str] = ""
    expected_output: Optional[str] = ""
    agent: Optional[str] = ""

    def __init__(self, name: str, path: Optional[Path] = None):
        if not path: path = Path()
        
        if not os.path.exists(path/TASKS_FILENAME):
            os.makedirs((path/TASKS_FILENAME).parent, exist_ok=True)
            (path/TASKS_FILENAME).touch()
        
        try:
            with open(path/TASKS_FILENAME, 'r') as f:
                data = yaml.load(f) or {}
            data = data.get(name, {}) or {}
            super().__init__(**{**{'name': name}, **data})
        except YAMLError as e:
            # TODO format MarkedYAMLError lines/messages
            raise ValidationError(f"Error parsing tasks file: {filename}\n{e}")
        except pydantic.ValidationError as e:
            error_str = "Error validating tasks config:\n"
            for error in e.errors():
                error_str += f"{' '.join(error['loc'])}: {error['msg']}\n"
            raise ValidationError(f"Error loading task {name} from {filename}.\n{error_str}")
        
        # store the path *after* loading data
        self._path = path

    def model_dump(self, *args, **kwargs) -> dict:
        dump = super().model_dump(*args, **kwargs)
        dump.pop('name') # name is the key, so keep it out of the data
        # format these as FoldedScalarStrings
        for key in ('description', 'expected_output', 'agent'):
            dump[key] = FoldedScalarString(dump.get(key) or "")
        return {self.name: dump}

    def write(self):
        with open(self._path/TASKS_FILENAME, 'r') as f:
            data = yaml.load(f) or {}
        
        data.update(self.model_dump())
        
        with open(self._path/TASKS_FILENAME, 'w') as f:
            yaml.dump(data, f)
    
    def __enter__(self) -> 'AgentConfig': return self
    def __exit__(self, *args): self.write()
