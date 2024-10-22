import json
import shutil
import time
from datetime import datetime
from typing import Optional

from art import text2art
import inquirer
import os
import webbrowser
import importlib.resources
from cookiecutter.main import cookiecutter

from .agentstack_data import FrameworkData, ProjectMetadata, ProjectStructure, CookiecutterData
from agentstack.logger import log
from .. import generation
from ..utils import open_json_file, term_color


def init_project_builder(slug_name: Optional[str] = None, skip_wizard: bool = False):
    if skip_wizard:
        project_details = {
            "name": slug_name or "new_agentstack_project",
            "version": "0.1.0",
            "description": "New agentstack project",
            "author": "<NAME>",
            "license": "MIT"
        }

        framework = "CrewAI"  # TODO: if --no-wizard, require a framework flag

        design = {
            'agents': [],
            'tasks': []
        }

        tools = []
    else:
        welcome_message()
        project_details = ask_project_details(slug_name)
        welcome_message()
        framework = ask_framework()
        design = ask_design()
        tools = ask_tools()

    log.debug(
        f"project_details: {project_details}"
        f"framework: {framework}"
        f"design: {design}"
    )
    insert_template(project_details, framework, design)
    add_tools(tools, project_details['name'])


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
        agent = inquirer.prompt([
            inquirer.Text("name", message="What's the name of this agent? (snake_case)"),
            inquirer.Text("role", message="What role does this agent have?"),
            inquirer.Text("goal", message="What is the goal of the agent?"),
            inquirer.Text("backstory", message="Give your agent a backstory"),
            # TODO: make a list #2
            inquirer.Text('model', message="What LLM should this agent use? (any LiteLLM provider)", default="openai/gpt-4"),
            # inquirer.List("model", message="What LLM should this agent use? (any LiteLLM provider)", choices=[
            #     'mixtral_llm',
            #     'mixtral_llm',
            # ]),
            inquirer.Confirm(
                "another",
                message="Create another agent?"
            ),
        ])

        make_agent = agent['another']
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
        task = inquirer.prompt([
            inquirer.Text("name", message="What's the name of this task?"),
            inquirer.Text("description", message="Describe the task in more detail"),
            inquirer.Text("expected_output",
                          message="What do you expect the result to look like? (ex: A 5 bullet point summary of the email)"),
            inquirer.List("agent", message="Which agent should be assigned this task?",
                          choices=[a['name'] for a in agents], ),
            inquirer.Confirm(
                "another",
                message="Create another task?"
            ),
        ])

        make_task = task['another']
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
    questions = [
        inquirer.Text("name", message="What's the name of your project (snake_case)", default=slug_name or ''),
        inquirer.Text("version", message="What's the initial version", default="0.1.0"),
        inquirer.Text("description", message="Enter a description for your project"),
        inquirer.Text("author", message="Who's the author (your name)?"),
        inquirer.List(
            "license",
            message="License?",
            choices=[
                "MIT",
                "Apache-2.0",
                "GPL",
                "other",
            ],
        ),
    ]

    return inquirer.prompt(questions)


def insert_template(project_details: dict, framework_name: str, design: dict):
    framework = FrameworkData(framework_name.lower())
    project_metadata = ProjectMetadata(project_name=project_details["name"],
                                       description=project_details["description"],
                                       author_name=project_details["author"],
                                       version=project_details["version"],
                                       license=project_details["license"],
                                       year=datetime.now().year)

    project_structure = ProjectStructure()
    project_structure.agents = design["agents"]
    project_structure.tasks = design["tasks"]

    cookiecutter_data = CookiecutterData(project_metadata=project_metadata,
                                         structure=project_structure,
                                         framework=framework_name.lower())

    with importlib.resources.path(f'agentstack.templates', str(framework.name)) as template_path:
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
        "    poetry run python src/main.py\n\n"
        "  Run `agentstack --help` for help!\n"
    )


def add_tools(tools: list, project_name: str):
    for tool in tools:
        generation.add_tool(tool, project_name)


def list_tools():
    with importlib.resources.path(f'agentstack.tools', 'tools.json') as tools_json_path:
        try:
            # Load the JSON data
            tools_data = open_json_file(tools_json_path)

            # Display the tools
            print("\n\nAvailable AgentStack Tools:")
            for category, tools in tools_data.items():
                print(f"\n{category.capitalize()}:")
                for tool in tools:
                    print(f"  - {tool['name']}: {tool['url']}")

            print("\n\n✨ Add a tool with: agentstack tools add <tool_name>")

        except FileNotFoundError:
            print("Error: tools.json file not found at path:", tools_json_path)
        except json.JSONDecodeError:
            print("Error: tools.json contains invalid JSON.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")