import json
import sys
from datetime import datetime

from art import text2art
import inquirer
import os
import webbrowser
import subprocess


def init_project_builder():
    welcome_message()
    project_details = ask_project_details()

    create_project(project_details)

    welcome_message()
    stack = ask_stack()
    insert_template(project_details, stack)


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

def insert_template(project_details: dict, stack: dict):
    framework = stack["framework"].lower()
    slug = project_details["name"].lower().replace(" ", "_").replace("-", "_")

    variables = {
        "project_name": project_details["name"],
        "project_slug": slug,
        "description": project_details["description"],
        "author_name": project_details["author"],
        "version": project_details["version"],
        "license": project_details["license"],
        "year": datetime.now().year,
        "framework": framework,
    }

    with open(f"templates/{framework}/cookiecutter.json", "w") as json_file:
        json.dump(variables, json_file)

    current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    relative_path = os.path.relpath(current_dir, os.getcwd())
    project_path = relative_path + "/" + slug

    # try:
    #     os.makedirs(project_path, exist_ok=False)
    # except FileExistsError:
    #     print(
    #         f"Another project exists at this directory. Maybe try: agentstack init <directory>"
    #     )
    # except:
    #     print(
    #         f"Could not create project directory {project_path}. Does the project already exist?"
    #     )

    os.system(f"cookiecutter {relative_path}/templates/{framework} --no-input")

    subprocess.check_output(["git", "init"], cwd=project_path)
    subprocess.check_output(["git", "add", "."], cwd=project_path)
