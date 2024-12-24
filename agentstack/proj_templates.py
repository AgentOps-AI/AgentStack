from typing import Optional, Literal
import os, sys
from pathlib import Path
import pydantic
import requests
import json
from agentstack.exceptions import ValidationError
from agentstack.utils import get_package_path


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

    def to_v2(self) -> 'TemplateConfig_v2':
        return TemplateConfig_v2(
            name=self.name,
            description=self.description,
            template_version=2,
            framework=self.framework,
            method=self.method,
            agents=[TemplateConfig_v2.Agent(**agent) for agent in self.agents],
            tasks=[TemplateConfig_v2.Task(**task) for task in self.tasks],
            tools=[TemplateConfig_v2.Tool(**tool) for tool in self.tools],
            inputs={key: "" for key in self.inputs},
        )


class TemplateConfig_v2(pydantic.BaseModel):
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
    template_version: Literal[2]
    framework: str
    method: str
    agents: list[Agent]
    tasks: list[Task]
    tools: list[Tool]
    inputs: dict[str, str]

    def to_v3(self) -> 'TemplateConfig':
        return TemplateConfig(
            name=self.name,
            description=self.description,
            template_version=3,
            framework=self.framework,
            method=self.method,
            manager_agent=None,
            agents=[TemplateConfig.Agent(**agent.dict()) for agent in self.agents],
            tasks=[TemplateConfig.Task(**task.dict()) for task in self.tasks],
            tools=[TemplateConfig.Tool(**tool.dict()) for tool in self.tools],
            inputs=self.inputs,
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
    manager_agent: Optional[str]
        The name of the agent that manages the project.
    agents: list[TemplateConfig.Agent]
        A list of agents used by the project.
    tasks: list[TemplateConfig.Task]
        A list of tasks used by the project.
    tools: list[TemplateConfig.Tool]
        A list of tools used by the project.
    inputs: list[str]
        A list of inputs used by the project.
    """

    class Agent(pydantic.BaseModel):
        name: str
        role: str
        goal: str
        backstory: str
        allow_delegation: bool = False
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
    template_version: Literal[3]
    framework: str
    method: str
    manager_agent: Optional[str]
    agents: list[Agent]
    tasks: list[Task]
    tools: list[Tool]
    inputs: dict[str, str]

    def write_to_file(self, filename: Path):
        if not filename.suffix == '.json':
            filename = filename.with_suffix('.json')

        with open(filename, 'w') as f:
            model_dump = self.model_dump()
            f.write(json.dumps(model_dump, indent=4))

    @classmethod
    def from_template_name(cls, name: str) -> 'TemplateConfig':
        path = get_package_path() / f'templates/proj_templates/{name}.json'
        if not name in get_all_template_names():
            raise ValidationError(f"Template {name} not bundled with agentstack.")
        return cls.from_file(path)

    @classmethod
    def from_file(cls, path: Path) -> 'TemplateConfig':
        if not os.path.exists(path):
            raise ValidationError(f"Template {path} not found.")
        with open(path, 'r') as f:
            return cls.from_json(json.load(f))

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
                    return TemplateConfig_v1(**data).to_v2().to_v3()
                case 2:
                    return TemplateConfig_v2(**data).to_v3()
                case 3:
                    return cls(**data)  # current version
                case _:
                    raise ValidationError(f"Unsupported template version: {data.get('template_version')}")
        except pydantic.ValidationError as e:
            err_msg = "Error validating template config JSON:\n"
            for error in e.errors():
                err_msg += f"{' '.join([str(loc) for loc in error['loc']])}: {error['msg']}\n"
            raise ValidationError(err_msg)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Error decoding template JSON.\n{e}")


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
