import json
import sys
import time
from datetime import datetime

from art import text2art
import inquirer
import os
import webbrowser
import subprocess

from cli.agentstack_data import FrameworkData, ProjectMetadata, ProjectStructure, CookiecutterData


def init_project_builder():
    welcome_message()
    project_details = ask_project_details()

    create_project(project_details)

    welcome_message()
    stack = ask_stack()
    design = ask_design()
    insert_template(project_details, stack, design)


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


def ask_stack():
    framework = inquirer.prompt(
        [
            inquirer.List(
                "framework",
                message="What agent framework do you want to use?",
                choices=["CrewAI", "Autogen", "LiteLLM", "Learn what these are (link)"],
            )
        ]
    )
    if framework["framework"] == "Learn what these are (link)":
        webbrowser.open("https://youtu.be/xvFZjo5PgG0")
        framework = inquirer.prompt(
            [
                inquirer.List(
                    "framework",
                    message="What agent framework do you want to use?",
                    choices=["CrewAI", "Autogen", "LiteLLM"],
                )
            ]
        )

    use_tools = inquirer.prompt(
        [
            inquirer.Confirm(
                "use_tools",
                message="Do you want to use any tools?",
            )
        ]
    )

    browsing_tools = {}
    rag_tools = {}
    if use_tools["use_tools"]:
        browsing_tools = inquirer.prompt(
            [
                inquirer.Checkbox(
                    "browsing_tools",
                    message="Select browsing tools",
                    choices=[
                        "browserbasehq",
                        "firecrawl",
                        "MultiOn_AI",
                        "Crawl4AI",
                    ],
                )
            ]
        )

        rag_tools = inquirer.prompt(
            [
                inquirer.Checkbox(
                    "rag",
                    message="RAG/document loading",
                    choices=[
                        "Mem0ai",
                        "llama_index",
                    ],
                )
            ]
        )

    return {**framework, **browsing_tools, **rag_tools}


def ask_design() -> dict:
    use_wizard = inquirer.prompt(
        [
            inquirer.Confirm(
                "use_wizard",
                message="Would you like to use the CLI wizard to set up agents and tasks?",
            )
        ]
    )

    if not use_wizard['use_wizard']:
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
            inquirer.Text("name", message="What's the name of this agent?"),
            inquirer.Text("role", message="What role does this agent have?"),
            inquirer.Text("goal", message="What is the goal of the agent?"),
            inquirer.Text("backstory", message="Give your agent a backstory"),
            # TODO: make a list
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

    print(tasks)
    print(agents)

    return {'tasks': tasks, 'agents': agents}


def ask_project_details():
    questions = [
        inquirer.Text("name", message="What's the name of your project"),
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


def create_project(directory: str):
    # Create project folder structure
    try:
        if directory[-1] != ".":
            os.makedirs(directory, exist_ok=False)
    except FileExistsError:
        print(
            f"Another project exists at this directory. Maybe try: agentstack init <directory>"
        )
    except:
        print(
            f"Could not create project directory {directory}. Does the project already exist?"
        )


def insert_template(project_details: dict, stack: dict, design: dict):
    framework = FrameworkData(stack["framework"].lower())
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
                                         framework=stack["framework"].lower())

    with open(f"templates/{framework.name}/cookiecutter.json", "w") as json_file:
        json.dump(cookiecutter_data.to_dict(), json_file)

    current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    relative_path = os.path.relpath(current_dir, os.getcwd())
    project_path = relative_path + "/" + cookiecutter_data.project_metadata.project_slug

    os.system(f"cookiecutter {relative_path}/templates/{framework.name} --no-input")

    subprocess.check_output(["git", "init"], cwd=project_path)
    subprocess.check_output(["git", "add", "."], cwd=project_path)


def list_tools():
    try:
        # Determine the path to the tools.json file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        tools_json_path = os.path.join(script_dir, '..', 'tools', 'tools.json')

        # Load the JSON data
        with open(tools_json_path, 'r') as f:
            tools_data = json.load(f)

        # Display the tools
        print("\n\nAvailable AgentStack Tools:")
        for category, tools in tools_data.items():
            print(f"\n{category.capitalize()}:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['url']}")

        print("\n\n❇️ Add a tool with: agentstack tools add <tool_name>")

    except FileNotFoundError:
        print("Error: tools.json file not found at path:", tools_json_path)
    except json.JSONDecodeError:
        print("Error: tools.json contains invalid JSON.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")