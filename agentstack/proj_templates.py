from typing import Optional, Literal
import os, sys
from pathlib import Path
import pydantic
import requests
from agentstack import ValidationError
from agentstack.utils import get_package_path, open_json_file, term_color


class TemplateConfig_v1(pydantic.BaseModel):
    name: str
    description: str
    template_version: Literal[1]
    framework: str
    method: str
    agents: list[dict]
    tasks: list[dict]
    tools: list[dict]
    inputs: list[str]

    def to_v2(self) -> 'TemplateConfig':
        return TemplateConfig(
            name=self.name,
            description=self.description,
            template_version=2,
            framework=self.framework,
            method=self.method,
            agents=self.agents,
            tasks=self.tasks,
            tools=self.tools,
            inputs={key: "" for key in self.inputs},
        )


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
    inputs: dict[str, str]
        A list of inputs and values used by the project.
    """

    name: str
    description: str
    template_version: Literal[2]
    framework: str
    method: str
    agents: list[dict]
    tasks: list[dict]
    tools: list[dict]
    inputs: dict[str, str]

    @classmethod
    def from_template_name(cls, name: str) -> 'TemplateConfig':
        path = get_package_path() / f'templates/proj_templates/{name}.json'
        if not os.path.exists(path):  # TODO raise exceptions and handle message/exit in cli
            print(term_color(f'No known agentstack tool: {name}', 'red'))
            sys.exit(1)
        return cls.from_file(path)

    @classmethod
    def from_file(cls, path: Path) -> 'TemplateConfig':
        return cls.from_json(open_json_file(path))

    @classmethod
    def from_url(cls, url: str) -> 'TemplateConfig':
        if not url.startswith("https://"):
            raise ValidationError(f"Invalid URL: {url}")
        response = requests.get(url)
        if response.status_code != 200:
            raise ValidationError(f"Failed to fetch template from {url}")
        return cls.from_json(response.json())

    @classmethod
    def from_json(cls, data: dict) -> 'TemplateConfig':
        try:
            match data.get('template_version'):
                case 1:
                    return TemplateConfig_v1(**data).to_v2()
                case 2:
                    return cls(**data)  # current version
                case _:
                    raise ValidationError(f"Unsupported template version: {data.get('template_version')}")
        except pydantic.ValidationError as e:
            # TODO raise exceptions and handle message/exit in cli
            print(term_color(f"Error validating template config JSON: \n{path}", 'red'))
            for error in e.errors():
                print(f"{' '.join([str(loc) for loc in error['loc']])}: {error['msg']}")
            sys.exit(1)


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
    return [TemplateConfig.from_file(path) for path in get_all_template_paths()]
