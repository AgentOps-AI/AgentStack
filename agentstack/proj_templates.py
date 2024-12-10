from typing import Optional
import os, sys
from pathlib import Path
import pydantic
import requests
from agentstack import ValidationError
from agentstack.utils import get_package_path, open_json_file, term_color


class TemplateConfig(pydantic.BaseModel):
    """
    Interface for interacting with template configuration files.

    Templates are read-only.

    Template Schema
    -------------
    name: str
        The name of the project.
    description: str
        A description of the template.
    template_version: int
        The version of the template.
    framework: str
        The framework the template is for.
    method: str
        The method used by the project. ie. "sequential"
    agents: list[dict]
        A list of agents used by the project. TODO vaidate this against an agent schema
    tasks: list[dict]
        A list of tasks used by the project. TODO validate this against a task schema
    tools: list[dict]
        A list of tools used by the project. TODO validate this against a tool schema
    inputs: list[str]
        A list of inputs used by the project.
    """

    class Agent(pydantic.BaseModel):
        name: str
        role: str
        goal: str
        backstory: str
        model: str

    class Task(pydantic.BaseModel):
        name: str
        description: str
        expected_output: str
        agent: str

    class Tool(pydantic.BaseModel):
        name: str
        agents: list[str]

    name: str
    description: str
    template_version: int = 1
    framework: str
    method: str = "sequential"
    agents: list[Agent]
    tasks: list[Task]
    tools: list[Tool]
    inputs: list[str]

    def write_to_file(self, filename: Path):
        with open(filename, 'w') as f:
            f.write(self.model_dump_json(indent=4))

    @classmethod
    def from_template_name(cls, name: str) -> 'TemplateConfig':
        path = get_package_path() / f'templates/proj_templates/{name}.json'
        if not os.path.exists(path):  # TODO raise exceptions and handle message/exit in cli
            print(term_color(f'No known agentstack tool: {name}', 'red'))
            sys.exit(1)
        return cls.from_json(path)

    @classmethod
    def from_json(cls, path: Path) -> 'TemplateConfig':
        data = open_json_file(path)
        try:
            return cls(**data)
        except pydantic.ValidationError as e:
            # TODO raise exceptions and handle message/exit in cli
            print(term_color(f"Error validating template config JSON: \n{path}", 'red'))
            for error in e.errors():
                print(f"{' '.join([str(loc) for loc in error['loc']])}: {error['msg']}")
            sys.exit(1)

    @classmethod
    def from_url(cls, url: str) -> 'TemplateConfig':
        if not url.startswith("https://"):
            raise ValidationError(f"Invalid URL: {url}")
        response = requests.get(url)
        if response.status_code != 200:
            raise ValidationError(f"Failed to fetch template from {url}")
        return cls(**response.json())


def get_all_template_paths() -> list[Path]:
    paths = []
    templates_dir = get_package_path() / 'templates/proj_templates'
    for file in templates_dir.iterdir():
        if file.suffix == '.json':
            paths.append(file)
    return paths


def get_all_template_names() -> list[str]:
    return [path.stem for path in get_all_template_paths()]


def get_all_templates() -> list[TemplateConfig]:
    return [TemplateConfig.from_json(path) for path in get_all_template_paths()]
