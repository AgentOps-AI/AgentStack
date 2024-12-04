import json
import shutil
import sys
import time
from datetime import datetime
from typing import Optional
import requests
import itertools

from art import text2art
import inquirer
import os
import importlib.resources
from cookiecutter.main import cookiecutter

from .agentstack_data import FrameworkData, ProjectMetadata, ProjectStructure, CookiecutterData
from agentstack.logger import log
from agentstack.utils import get_package_path
from agentstack.generation.files import ConfigFile
from agentstack.generation.tool_generation import get_all_tools
from agentstack import packaging, generation
from agentstack.utils import open_json_file, term_color, is_snake_case
from agentstack.update import AGENTSTACK_PACKAGE

PREFERRED_MODELS = [
    'openai/gpt-4o',
    'anthropic/claude-3-5-sonnet',
    'openai/o1-preview',
    'openai/gpt-4-turbo',
    'anthropic/claude-3-opus',
]

def init_project_builder(slug_name: Optional[str] = None, template: Optional[str] = None, use_wizard: bool = False):
    if slug_name and not is_snake_case(slug_name):
        print(term_color("Project name must be snake case", 'red'))
        return

    if template is not None and use_wizard:
        print(term_color("Template and wizard flags cannot be used together", 'red'))
        return

    template_data = None
    if template is not None:
        url_start = "https://"
        if template[:len(url_start)] == url_start:
            # template is a url
            response = requests.get(template)
            if response.status_code == 200:
                template_data = response.json()
            else:
                print(term_color(f"Failed to fetch template data from {template}. Status code: {response.status_code}", 'red'))
                sys.exit(1)
        else:
            with importlib.resources.path('agentstack.templates.proj_templates', f'{template}.json') as template_path:
                if template_path is None:
                    print(term_color(f"No such template {template} found", 'red'))
                    sys.exit(1)
                template_data = open_json_file(template_path)

    if template_data:
        project_details = {
            "name": slug_name or template_data['name'],
            "version": "0.0.1",
            "description": template_data['description'],
            "author": "Name <Email>",
            "license": "MIT"
        }
        framework = template_data['framework']
        design = {
            'agents': template_data['agents'],
            'tasks': template_data['tasks'],
            'inputs': template_data['inputs'],
        }

        tools = template_data['tools']

    elif use_wizard:
        welcome_message()
        project_details = ask_project_details(slug_name)
        welcome_message()
        framework = ask_framework()
        design = ask_design()
        tools = ask_tools()

    else:
        welcome_message()
        project_details = {
            "name": slug_name or "agentstack_project",
            "version": "0.0.1",
            "description": "New agentstack project",
            "author": "Name <Email>",
            "license": "MIT"
        }

        framework = "crewai"  # TODO: if --no-wizard, require a framework flag

        design = {
            'agents': [],
            'tasks': [],
            'inputs': []
        }

        tools = []

    log.debug(
        f"project_details: {project_details}"
        f"framework: {framework}"
        f"design: {design}"
    )
    insert_template(project_details, framework, design, template_data)
    for tool_data in tools:
        generation.add_tool(tool_data['name'], agents=tool_data['agents'], path=project_details['name'])

    try:
        packaging.install(f'{AGENTSTACK_PACKAGE}[{framework}]', path=slug_name)
    except Exception as e:
        print(term_color(f"Failed to install dependencies for {slug_name}. Please try again by running `agentstack update`", 'red'))


def welcome_message():
    os.system("cls" if os.name == "nt" else "clear")
    title = text2art("AgentStack", font="smisome1")
    tagline = "The easiest way to build a robust agent application!"
    border = "-" * len(tagline)

    # Print the welcome message with ASCII art
    print(title)
    print(border)
    print(tagline)
    print(border)


def configure_default_model(path: Optional[str] = None):
    """Set the default model"""
    agentstack_config = ConfigFile(path)
    if agentstack_config.default_model:
        return # Default model already set
    
    print("Project does not have a default model configured.")
    other_msg = f"Other (enter a model name)"
    model = inquirer.list_input(
        message="Which model would you like to use?",
        choices=PREFERRED_MODELS + [other_msg],
    )

    if model == other_msg: # If the user selects "Other", prompt for a model name
        print(f'A list of available models is available at: "https://docs.litellm.ai/docs/providers"')
        model = inquirer.text(message="Enter the model name")
    
    with ConfigFile(path) as agentstack_config:
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

    print("Congrats! Your project is ready to go! Quickly add features now or skip to do it later.\n\n")

    return framework


def ask_design() -> dict:
    use_wizard = inquirer.confirm(
        message="Would you like to use the CLI wizard to set up agents and tasks?",
    )

    if not use_wizard:
        return {
            'agents': [],
            'tasks': []
        }

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

        agent_incomplete = True
        agent = None
        while agent_incomplete:
            agent = inquirer.prompt([
                inquirer.Text("name", message="What's the name of this agent? (snake_case)"),
                inquirer.Text("role", message="What role does this agent have?"),
                inquirer.Text("goal", message="What is the goal of the agent?"),
                inquirer.Text("backstory", message="Give your agent a backstory"),
                # TODO: make a list - #2
                inquirer.Text('model', message="What LLM should this agent use? (any LiteLLM provider)", default="openai/gpt-4"),
                # inquirer.List("model", message="What LLM should this agent use? (any LiteLLM provider)", choices=[
                #     'mixtral_llm',
                #     'mixtral_llm',
                # ]),
            ])

            if not agent['name'] or agent['name'] == '':
                print(term_color("Error: Agent name is required - Try again", 'red'))
                agent_incomplete = True
            elif not is_snake_case(agent['name']):
                print(term_color("Error: Agent name must be snake case - Try again", 'red'))
            else:
                agent_incomplete = False

        make_agent = inquirer.confirm(message="Create another agent?")
        agents.append(agent)

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

        task_incomplete = True
        task = None
        while task_incomplete:
            task = inquirer.prompt([
                inquirer.Text("name", message="What's the name of this task? (snake_case)"),
                inquirer.Text("description", message="Describe the task in more detail"),
                inquirer.Text("expected_output",
                              message="What do you expect the result to look like? (ex: A 5 bullet point summary of the email)"),
                inquirer.List("agent", message="Which agent should be assigned this task?",
                              choices=[a['name'] for a in agents], ),
            ])

            if not task['name'] or task['name'] == '':
                print(term_color("Error: Task name is required - Try again", 'red'))
            elif not is_snake_case(task['name']):
                print(term_color("Error: Task name must be snake case - Try again", 'red'))
            else:
                task_incomplete = False

        make_task = inquirer.confirm(message="Create another task?")
        tasks.append(task)

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
            choices=list(tools_data.keys()) + ["~~ Stop adding tools ~~"]
        )

        tools_in_cat = [f"{t['name']} - {t['url']}" for t in tools_data[tool_type] if t not in tools_to_add]
        tool_selection = inquirer.list_input(
            message="Select your tool",
            choices=tools_in_cat
        )

        tools_to_add.append(tool_selection.split(' - ')[0])

        print("Adding tools:")
        for t in tools_to_add:
            print(f'  - {t}')
        print('')
        adding_tools = inquirer.confirm("Add another tool?")

    return tools_to_add


def ask_project_details(slug_name: Optional[str] = None) -> dict:
    name = inquirer.text(message="What's the name of your project (snake_case)", default=slug_name or '')

    if not is_snake_case(name):
        print(term_color("Project name must be snake case", 'red'))
        return ask_project_details(slug_name)

    questions = inquirer.prompt([
        inquirer.Text("version", message="What's the initial version", default="0.1.0"),
        inquirer.Text("description", message="Enter a description for your project"),
        inquirer.Text("author", message="Who's the author (your name)?"),
    ])

    questions['name'] = name

    return questions


def insert_template(project_details: dict, framework_name: str, design: dict, template_data: Optional[dict] = None):
    framework = FrameworkData(framework_name.lower())
    project_metadata = ProjectMetadata(project_name=project_details["name"],
                                       description=project_details["description"],
                                       author_name=project_details["author"],
                                       version="0.0.1",
                                       license="MIT",
                                       year=datetime.now().year,
                                       template=template_data['name'] if template_data else None,
                                       template_version=template_data['template_version'] if template_data else None)

    project_structure = ProjectStructure()
    project_structure.agents = design["agents"]
    project_structure.tasks = design["tasks"]
    project_structure.set_inputs(design["inputs"])

    cookiecutter_data = CookiecutterData(project_metadata=project_metadata,
                                         structure=project_structure,
                                         framework=framework_name.lower())

    template_path = get_package_path() / f'templates/{framework.name}'
    with open(f"{template_path}/cookiecutter.json", "w") as json_file:
        json.dump(cookiecutter_data.to_dict(), json_file)

    # copy .env.example to .env
    shutil.copy(
        f'{template_path}/{"{{cookiecutter.project_metadata.project_slug}}"}/.env.example',
        f'{template_path}/{"{{cookiecutter.project_metadata.project_slug}}"}/.env')

    if os.path.isdir(project_details['name']):
        print(term_color(f"Directory {template_path} already exists. Please check this and try again", "red"))
        return

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

    # TODO: check if poetry is installed and if so, run poetry install in the new directory
    # os.system("poetry install")
    # os.system("cls" if os.name == "nt" else "clear")
    # TODO: add `agentstack docs` command
    print(
        "\n"
        "🚀 \033[92mAgentStack project generated successfully!\033[0m\n\n"
        "  Next, run:\n"
        f"    cd {project_metadata.project_slug}\n"
        "    poetry install\n"
        "    agentstack run\n\n"
        "  Add agents and tasks with:\n"
        "    `agentstack generate agent/task <name>`\n\n"
        "  Run `agentstack quickstart` or `agentstack docs` for next steps.\n"
    )


def list_tools():
    # Display the tools
    tools = get_all_tools()
    curr_category = None

    print("\n\nAvailable AgentStack Tools:")
    for category, tools in itertools.groupby(tools, lambda x: x.category):
        if curr_category != category:
            print(f"\n{category}:")
            curr_category = category
        for tool in tools:
            print("  - ", end='')
            print(term_color(f"{tool.name}", 'blue'), end='')
            print(f": {tool.url if tool.url else 'AgentStack default tool'}")

    print("\n\n✨ Add a tool with: agentstack tools add <tool_name>")
    print("   https://docs.agentstack.sh/tools/core")