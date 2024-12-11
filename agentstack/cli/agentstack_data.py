import json
from datetime import datetime
from typing import Optional

from agentstack.utils import clean_input, get_version
from agentstack.logger import log


class ProjectMetadata:
    def __init__(
        self,
        project_name: Optional[str] = None,
        project_slug: Optional[str] = None,
        description: str = "",
        author_name: str = "",
        version: str = "",
        license: str = "",
        year: int = datetime.now().year,
        template: str = "none",
        template_version: int = 0,
    ):
        self.project_name = clean_input(project_name) if project_name else "myagent"
        self.project_slug = clean_input(project_slug) if project_slug else self.project_name
        self.description = description
        self.author_name = author_name
        self.version = version
        self.license = license
        self.year = year
        self.agentstack_version = get_version()
        self.template = template
        self.template_version = template_version

        log.debug(f"ProjectMetadata: {self.to_dict()}")

    def to_dict(self):
        return {
            'project_name': self.project_name,
            'project_slug': self.project_slug,
            'description': self.description,
            'author_name': self.author_name,
            'version': self.version,
            'license': self.license,
            'year': self.year,
            'agentstack_version': self.agentstack_version,
            'template': self.template,
            'template_version': self.template_version,
        }

    def to_json(self):
        return json.dumps(self.to_dict(), default=str)


class ProjectStructure:
    def __init__(self):
        self.agents = []
        self.tasks = []
        self.inputs = []

    def add_agent(self, agent):
        self.agents.append(agent)

    def add_task(self, task):
        self.tasks.append(task)

    def set_inputs(self, inputs):
        self.inputs = inputs

    def to_dict(self):
        return {
            'agents': self.agents,
            'tasks': self.tasks,
            'inputs': self.inputs,
        }

    def to_json(self):
        return json.dumps(self.to_dict(), default=str)


class FrameworkData:
    def __init__(
        self,
        # name: Optional[Literal["crewai"]] = None
        name: Optional[str] = None,  # TODO: better framework handling, Literal or Enum
    ):
        self.name = name

    def to_dict(self):
        return {
            'name': self.name,
        }

    def to_json(self):
        return json.dumps(self.to_dict(), default=str)


class CookiecutterData:
    def __init__(
        self,
        project_metadata: ProjectMetadata,
        structure: ProjectStructure,
        # framework: Literal["crewai"],
        framework: str,
    ):
        self.project_metadata = project_metadata
        self.framework = framework
        self.structure = structure

    def to_dict(self):
        return {
            'project_metadata': self.project_metadata.to_dict(),
            'framework': self.framework,
            'structure': self.structure.to_dict(),
        }

    def to_json(self):
        return json.dumps(self.to_dict(), default=str)
