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
    template_version: str
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

    name: str
    description: str
    template_version: int
    framework: str
    method: str
    agents: list[dict]
    tasks: list[dict]
    tools: list[dict]
    inputs: list[str]

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
