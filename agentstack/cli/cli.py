from typing import Optional
import os
import sys
import time
from datetime import datetime

import json
import shutil
from art import text2art
import inquirer
from cookiecutter.main import cookiecutter

from .agentstack_data import (
    FrameworkData,
    ProjectMetadata,
    ProjectStructure,
    CookiecutterData,
)
from agentstack import conf, log
from agentstack.conf import ConfigFile
from agentstack.utils import get_package_path
from agentstack.generation.files import ProjectFile
from agentstack import frameworks
from agentstack import generation
from agentstack import inputs
from agentstack.agents import get_all_agents
from agentstack.tasks import get_all_tasks
from agentstack.utils import open_json_file, term_color, is_snake_case, get_framework, validator_not_empty
from agentstack.proj_templates import TemplateConfig
from agentstack.exceptions import ValidationError


PREFERRED_MODELS = [
    'openai/gpt-4o',
    'anthropic/claude-3-5-sonnet',
    'openai/o1-preview',
    'openai/gpt-4-turbo',
    'anthropic/claude-3-opus',
]


def init_project_builder(
    slug_name: Optional[str] = None,
    template: Optional[str] = None,
    framework: Optional[str] = None,
    use_wizard: bool = False,
):
    if not slug_name and not use_wizard:
        raise Exception("Project name is required. Use `agentstack init <project_name>`")

    if slug_name and not is_snake_case(slug_name):
        raise Exception("Project slug name must be snake_case")

    if template is not None and use_wizard:
        raise Exception("Template and wizard flags cannot be used together")

    template_data = None
    if template is not None:
        template_data = TemplateConfig.from_user_input(template)

    if template_data:
        project_details = {
            "name": slug_name or template_data.name,
            "version": "0.0.1",
            "description": template_data.description,
            "author": "Name <Email>",
            "license": "MIT",
        }
        if framework is None:
            framework = template_data.framework
        design = {
            'agents': [agent.model_dump() for agent in template_data.agents],
            'tasks': [task.model_dump() for task in template_data.tasks],
            'graph': [[node[0].model_dump(), node[1].model_dump()] for node in template_data.graph],
            'inputs': template_data.inputs,
        }
        tools = [tools.model_dump() for tools in template_data.tools]

    elif use_wizard:
        project_details = ask_project_details(slug_name)
        welcome_message()
        framework = ask_framework()
        design = ask_design()
        tools = ask_tools()

    else:
        # the user has started a new project; let's give them something to work with
        default_project = TemplateConfig.from_template_name('hello_alex')
        project_details = {
            "name": slug_name or default_project.name,
            "version": "0.0.1",
            "description": default_project.description,
            "author": "Name <Email>",
            "license": "MIT",
        }
        if framework is None:
            framework = default_project.framework
        design = {
            'agents': [agent.model_dump() for agent in default_project.agents],
            'tasks': [task.model_dump() for task in default_project.tasks],
            'graph': [[node[0].model_dump(), node[1].model_dump()] for node in default_project.graph],
            'inputs': default_project.inputs,
        }
        tools = [tools.model_dump() for tools in default_project.tools]

    log.debug(f"project_details: {project_details}" f"framework: {framework}" f"design: {design}")
    insert_template(project_details, framework, design, template_data)

    for tool_data in tools:
        generation.add_tool(tool_data['name'], agents=tool_data['agents'])


def welcome_message():
    title = text2art("AgentStack", font="smisome1")
    tagline = "The easiest way to build a robust agent application!"
    border = "-" * len(tagline)

    # Print the welcome message with ASCII art
    log.info(title)
    log.info(border)
    log.info(tagline)
    log.info(border)


def configure_default_model():
    """Set the default model"""
    agentstack_config = ConfigFile()
    if agentstack_config.default_model:
        log.debug("Using default model from project config.")
        return  # Default model already set

    log.info("Project does not have a default model configured.")
    other_msg = "Other (enter a model name)"
    model = inquirer.list_input(
        message="Which model would you like to use?",
        choices=PREFERRED_MODELS + [other_msg],
    )

    if model == other_msg:  # If the user selects "Other", prompt for a model name
        log.info('A list of available models is available at: "https://docs.litellm.ai/docs/providers"')
        model = inquirer.text(message="Enter the model name")

    log.debug("Writing default model to project config.")
    with ConfigFile() as agentstack_config:
        agentstack_config.default_model = model


def ask_framework() -> str:
    framework = "CrewAI"
    # framework = inquirer.list_input(
    #     message="What agent framework do you want to use?",
    #     choices=["CrewAI", "Autogen", "LiteLLM", "Learn what these are (link)"],
    # )
    #
    # if framework == "Learn what these are (link)":
    #     webbrowser.open("https://youtu.be/xvFZjo5PgG0")
    #     framework = inquirer.list_input(
    #         message="What agent framework do you want to use?",
    #         choices=["CrewAI", "Autogen", "LiteLLM"],
    #     )
    #
    # while framework in ['Autogen', 'LiteLLM']:
    #     print(f"{framework} support coming soon!!")
    #     framework = inquirer.list_input(
    #         message="What agent framework do you want to use?",
    #         choices=["CrewAI", "Autogen", "LiteLLM"],
    #     )

    log.success("Congrats! Your project is ready to go! Quickly add features now or skip to do it later.\n\n")

    return framework


def get_validated_input(
    message: str,
    validate_func=None,
    min_length: int = 0,
    snake_case: bool = False,
) -> str:
    """Helper function to get validated input from user.

    Args:
        message: The prompt message to display
        validate_func: Optional custom validation function
        min_length: Minimum length requirement (0 for no requirement)
        snake_case: Whether to enforce snake_case naming
    """
    while True:
        value = inquirer.text(
            message=message,
            validate=validate_func or validator_not_empty(min_length) if min_length else None,
        )
        if snake_case and not is_snake_case(value):
            raise ValidationError("Input must be in snake_case")
        return value


def ask_agent_details():
    agent = {}

    agent['name'] = get_validated_input(
        "What's the name of this agent? (snake_case)", min_length=3, snake_case=True
    )

    agent['role'] = get_validated_input("What role does this agent have?", min_length=3)

    agent['goal'] = get_validated_input("What is the goal of the agent?", min_length=10)

    agent['backstory'] = get_validated_input("Give your agent a backstory", min_length=10)

    agent['model'] = inquirer.list_input(
        message="What LLM should this agent use?", choices=PREFERRED_MODELS, default=PREFERRED_MODELS[0]
    )

    return agent


def ask_task_details(agents: list[dict]) -> dict:
    task = {}

    task['name'] = get_validated_input(
        "What's the name of this task? (snake_case)", min_length=3, snake_case=True
    )

    task['description'] = get_validated_input("Describe the task in more detail", min_length=10)

    task['expected_output'] = get_validated_input(
        "What do you expect the result to look like? (ex: A 5 bullet point summary of the email)",
        min_length=10,
    )

    task['agent'] = inquirer.list_input(
        message="Which agent should be assigned this task?",
        choices=[a['name'] for a in agents],
    )

    return task


def ask_design() -> dict:
    use_wizard = inquirer.confirm(
        message="Would you like to use the CLI wizard to set up agents and tasks?",
    )

    if not use_wizard:
        return {'agents': [], 'tasks': []}

    os.system("cls" if os.name == "nt" else "clear")

    title = text2art("AgentWizard", font="shimrod")

    print(title)

    print("""
🪄 welcome to the agent builder wizard!! 🪄

First we need to create the agents that will work together to accomplish tasks:
    """)
    make_agent = True
    agents = []
    while make_agent:
        print('---')
        print(f"Agent #{len(agents)+1}")
        agent = None
        agent = ask_agent_details()
        agents.append(agent)
        make_agent = inquirer.confirm(message="Create another agent?")

    print('')
    for x in range(3):
        time.sleep(0.3)
        print('.')
    print('Boom! We made some agents (ﾉ>ω<)ﾉ :｡･:*:･ﾟ’★,｡･:*:･ﾟ’☆')
    time.sleep(0.5)
    print('')
    print('Now lets make some tasks for the agents to accomplish!')
    print('')

    make_task = True
    tasks = []
    while make_task:
        print('---')
        print(f"Task #{len(tasks) + 1}")
        task = ask_task_details(agents)
        tasks.append(task)
        make_task = inquirer.confirm(message="Create another task?")

    print('')
    for x in range(3):
        time.sleep(0.3)
        print('.')
    print('Let there be tasks (ノ ˘_˘)ノ　ζ|||ζ　ζ|||ζ　ζ|||ζ')

    return {'tasks': tasks, 'agents': agents}


def ask_tools() -> list:
    use_tools = inquirer.confirm(
        message="Do you want to add agent tools now? (you can do this later with `agentstack tools add <tool_name>`)",
    )

    if not use_tools:
        return []

    tools_to_add = []

    adding_tools = True
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tools_json_path = os.path.join(script_dir, '..', 'tools', 'tools.json')

    # Load the JSON data
    tools_data = open_json_file(tools_json_path)

    while adding_tools:
        tool_type = inquirer.list_input(
            message="What category tool do you want to add?",
            choices=list(tools_data.keys()) + ["~~ Stop adding tools ~~"],
        )

        tools_in_cat = [f"{t['name']} - {t['url']}" for t in tools_data[tool_type] if t not in tools_to_add]
        tool_selection = inquirer.list_input(message="Select your tool", choices=tools_in_cat)

        tools_to_add.append(tool_selection.split(' - ')[0])

        log.info("Adding tools:")
        for t in tools_to_add:
            log.info(f'  - {t}')
        log.info('')
        adding_tools = inquirer.confirm("Add another tool?")

    return tools_to_add


def ask_project_details(slug_name: Optional[str] = None) -> dict:
    name = inquirer.text(message="What's the name of your project (snake_case)", default=slug_name or '')

    if not is_snake_case(name):
        log.error("Project name must be snake case")
        return ask_project_details(slug_name)

    questions = inquirer.prompt(
        [
            inquirer.Text("version", message="What's the initial version", default="0.1.0"),
            inquirer.Text("description", message="Enter a description for your project"),
            inquirer.Text("author", message="Who's the author (your name)?"),
        ]
    )

    questions['name'] = name

    return questions


def insert_template(
    project_details: dict,
    framework_name: str,
    design: dict,
    template_data: Optional[TemplateConfig] = None,
):
    framework = FrameworkData(
        name=framework_name.lower(),
    )
    project_metadata = ProjectMetadata(
        project_name=project_details["name"],
        description=project_details["description"],
        author_name=project_details["author"],
        version="0.0.1",
        license="MIT",
        year=datetime.now().year,
        template=template_data.name if template_data else 'none',
        template_version=template_data.template_version if template_data else 0,
    )

    project_structure = ProjectStructure(
        method=template_data.method if template_data else "sequential",
        manager_agent=template_data.manager_agent if template_data else None,
    )
    project_structure.agents = design["agents"]
    project_structure.tasks = design["tasks"]
    project_structure.inputs = design["inputs"]
    project_structure.graph = design.get("graph", [])

    cookiecutter_data = CookiecutterData(
        project_metadata=project_metadata,
        structure=project_structure,
        framework=framework_name.lower(),
    )

    template_path = get_package_path() / f'templates/{framework.name}'
    with open(f"{template_path}/cookiecutter.json", "w") as json_file:
        json.dump(cookiecutter_data.to_dict(), json_file)
        # TODO this should not be written to the package directory

    # copy .env.example to .env
    shutil.copy(
        f'{template_path}/{"{{cookiecutter.project_metadata.project_slug}}"}/.env.example',
        f'{template_path}/{"{{cookiecutter.project_metadata.project_slug}}"}/.env',
    )

    cookiecutter(str(template_path), no_input=True, extra_context=None)

    # TODO: inits a git repo in the directory the command was run in
    # TODO: not where the project is generated. Fix this
    # TODO: also check if git is installed or if there are any git repos above the current dir
    try:
        pass
        # subprocess.check_output(["git", "init"])
        # subprocess.check_output(["git", "add", "."])
    except:
        print("Failed to initialize git repository. Maybe you're already in one? Do this with: git init")


def export_template(output_filename: str):
    """
    Export the current project as a template.
    """
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
                model=agent.llm,  # TODO consistent naming (llm -> model)
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
    for agent_name in frameworks.get_agent_names():
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

    template = TemplateConfig(
        template_version=4,
        name=metadata.project_name,
        description=metadata.project_description,
        framework=get_framework(),
        method="sequential",  # TODO this needs to be stored in the project somewhere
        manager_agent=None,  # TODO
        agents=agents,
        tasks=tasks,
        tools=tools,
        inputs=inputs.get_inputs(),
        graph=[],  # TODO
    )

    try:
        template.write_to_file(conf.PATH / output_filename)
        log.success(f"Template saved to: {conf.PATH / output_filename}")
    except Exception as e:
        raise Exception(f"Failed to write template to file: {e}")
