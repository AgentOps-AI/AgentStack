from typing import Optional
from datetime import datetime
import json
import shutil
from cookiecutter.main import cookiecutter

from agentstack import conf, log
from agentstack.utils import get_package_path, get_framework
from agentstack import frameworks
from agentstack.agents import get_all_agents
from agentstack.tasks import get_all_tasks
from agentstack import inputs
from agentstack.templates import CURRENT_VERSION, TemplateConfig
from agentstack.generation.files import ProjectFile
from .agentstack_data import (
    FrameworkData,
    ProjectMetadata,
    ProjectStructure,
    CookiecutterData,
)


def insert_template(name: str, template: TemplateConfig, framework: Optional[str] = None):
    if framework is None:
        framework = template.framework
    
    framework_data = FrameworkData(
        name=framework,
    )
    project_metadata = ProjectMetadata(
        project_name=name,
        description=template.description,
        author_name="Name <Email>",
        version="0.0.1",
        license="MIT",
        year=datetime.now().year,
        template=template.name,
        template_version=template.template_version,
    )
    project_structure = ProjectStructure(
        method=template.method or "sequential",
        manager_agent=template.manager_agent or None,
    )
    project_structure.agents = [a.model_dump() for a in template.agents]
    project_structure.tasks = [t.model_dump() for t in template.tasks]
    project_structure.inputs = template.inputs
    project_structure.graph = [[e.model_dump() for e in n] for n in template.graph]

    cookiecutter_data = CookiecutterData(
        project_metadata=project_metadata,
        structure=project_structure,
        framework=framework,
    )

    template_path = get_package_path() / f'frameworks/templates/{framework}'
    with open(f"{template_path}/cookiecutter.json", "w") as json_file:
        json.dump(cookiecutter_data.to_dict(), json_file)
        # TODO this should not be written to the package directory

    # copy .env.example to .env
    shutil.copy(
        f'{template_path}/{"{{cookiecutter.project_metadata.project_slug}}"}/.env.example',
        f'{template_path}/{"{{cookiecutter.project_metadata.project_slug}}"}/.env',
    )
    cookiecutter(str(template_path), no_input=True, extra_context=None)


def export_template(output_filename: str):
    """
    Export the current project as a template.
    """
    conf.assert_project()
    
    try:
        metadata = ProjectFile()
    except Exception as e:
        raise Exception(f"Failed to load project metadata: {e}")

    # Read all the agents from the project's agents.yaml file
    agents: list[TemplateConfig.Agent] = []
    for agent in get_all_agents():
        agents.append(
            TemplateConfig.Agent(
                name=agent.name,
                role=agent.role,
                goal=agent.goal,
                backstory=agent.backstory,
                allow_delegation=False,  # TODO
                llm=agent.llm,
            )
        )

    # Read all the tasks from the project's tasks.yaml file
    tasks: list[TemplateConfig.Task] = []
    for task in get_all_tasks():
        tasks.append(
            TemplateConfig.Task(
                name=task.name,
                description=task.description,
                expected_output=task.expected_output,
                agent=task.agent,
            )
        )

    # Export all of the configured tools from the project
    tools_agents: dict[str, list[str]] = {}
    for agent_name in frameworks.get_agent_method_names():
        for tool_name in frameworks.get_agent_tool_names(agent_name):
            if not tool_name:
                continue
            if tool_name not in tools_agents:
                tools_agents[tool_name] = []
            tools_agents[tool_name].append(agent_name)

    tools: list[TemplateConfig.Tool] = []
    for tool_name, agent_names in tools_agents.items():
        tools.append(
            TemplateConfig.Tool(
                name=tool_name,
                agents=agent_names,
            )
        )
    
    # Export the graph structure from the project
    graph: list[list[TemplateConfig.Node]] = []
    for node in frameworks.get_graph():
        graph.append(
            [
                TemplateConfig.Node(
                    name=node.source.name,
                    type=node.source.type.value  # type: ignore
                ),
                TemplateConfig.Node(
                    name=node.target.name,
                    type=node.target.type.value  # type: ignore
                ),
            ]
        )

    template = TemplateConfig(
        template_version=CURRENT_VERSION,
        name=metadata.project_name,
        description=metadata.project_description,
        framework=get_framework(),
        method="sequential",  # TODO this needs to be stored in the project somewhere
        manager_agent=None,  # TODO
        agents=agents,
        tasks=tasks,
        tools=tools,
        inputs=inputs.get_inputs(),
        graph=graph,
    )

    try:
        template.write_to_file(conf.PATH / output_filename)
        log.success(f"Template saved to: {conf.PATH / output_filename}")
    except Exception as e:
        raise Exception(f"Failed to write template to file: {e}")
