import sys

from art import text2art

import inquirer
import os

def init_project_builder(directory: str):
    welcome_message()
    answers = ask_project_details()

    create_project(answers, directory)


def welcome_message():
    os.system('cls' if os.name == 'nt' else 'clear')
    title = text2art("AgentStack", font="send")
    tagline = "The easiest way to build a robust agent application!"
    border = '-' * len(tagline)

    # Print the welcome message with ASCII art
    print(title)
    print(border)
    print(tagline)
    print(border)


def ask_project_details():
    questions = [
        inquirer.Text('name', message="What's the name of your project"),
        inquirer.Text('version', message="What's the initial version", default="0.1.0"),
        inquirer.Text('description', message="Enter a description for your project"),
        inquirer.Text('author', message="Who's the author (your name)?"),
        inquirer.Text('license', message="License (e.g. MIT, Apache, GPL)", default="MIT"),
    ]

    answers = inquirer.prompt(questions)
    return answers


def create_project(answers, directory: str):
    # Create project folder structure
    try:
        if directory[-1] != '.':
            os.makedirs(directory, exist_ok=True)
    except:
        print(f"Could not create project directory {directory}")

    with open(f"{directory}/pyproject.toml", "w") as f:
        f.write(f"""
[tool.poetry]
name = "{answers['name']}"
version = "{answers['version']}"
description = "{answers['description']}"
authors = ["{answers['author']}"]
license = "{answers['license']}"

[tool.poetry.dependencies]
python = "^3.11"
agentops
""")
        # for dep in dependencies:
        #     f.write(f"{dep} = \"*\"\n")
