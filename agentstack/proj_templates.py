from typing import Optional, Literal
import os, sys
from pathlib import Path
import pydantic
import requests
import json
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
        A list of agents used by the project.
    tasks: list[dict]
        A list of tasks used by the project.
    tools: list[dict]
        A list of tools used by the project.
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
    template_version: Literal[1]
    framework: str
    method: str
    agents: list[Agent]
    tasks: list[Task]
    tools: list[Tool]
    inputs: list[str]

    def write_to_file(self, filename: Path):
        if not filename.suffix == '.json':
            filename = filename.with_suffix('.json')

        with open(filename, 'w') as f:
            model_dump = self.model_dump()
            f.write(json.dumps(model_dump, indent=4))

    @classmethod
    def from_template_name(cls, name: str) -> 'TemplateConfig':
        if name.startswith('https://'):
            return cls.from_url(name)
        if name.endswith('.json'):
            path = os.getcwd() / Path(name)
            if not path.exists():
                print(term_color(f'Template file does not exist: {path}', 'red'))
                sys.exit(1)
            return cls.from_json(path)
        path = get_package_path() / f'templates/proj_templates/{name}.json'
        if not os.path.exists(path):
            print(term_color(f'No known built-in template: {name}', 'red'))
            template_names = get_all_template_names()
            if not template_names:
                print(term_color(f'No built-in templates found at {path}', 'red'))
            else:
                print(term_color('Available built-in templates:', 'green'))
                for template in template_names:
                    print(term_color(f'    {template}', 'green'))
            sys.exit(1)
        return cls.from_json(path)

    @classmethod
    def from_json(cls, path: Path) -> 'TemplateConfig':
        data = open_json_file(path)
        try:
            return cls(**data)
        except pydantic.ValidationError as e:
            err_msg = "Error validating template config JSON: \n    {path}\n\n"
            for error in e.errors():
                err_msg += f"{' '.join([str(loc) for loc in error['loc']])}: {error['msg']}\n"
            raise ValidationError(err_msg)

    @classmethod
    def from_url(cls, url: str) -> 'TemplateConfig':
        if not url.startswith("https://"):
            raise ValidationError(f"Invalid URL: {url}")
        response = requests.get(url)
        if response.status_code != 200:
            raise ValidationError(f"Failed to fetch template from URL:\n    {url}")
        try:
            return cls(**response.json())
        except json.JSONDecodeError as e:
            raise ValidationError(f"Error decoding template JSON from URL:\n    {url}\n\n{e}")


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
