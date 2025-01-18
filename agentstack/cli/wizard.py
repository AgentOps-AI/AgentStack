from typing import Optional
import os
import time
import inquirer
import webbrowser
from art import text2art
from agentstack import log
from agentstack.utils import open_json_file, is_snake_case
from agentstack.cli import welcome_message, get_validated_input
from agentstack.proj_templates import TemplateConfig


def run_wizard(slug_name: str) -> TemplateConfig:
    raise NotImplementedError("TODO wizard functionality needs to be migrated")

    project_details = ask_project_details(slug_name)
    welcome_message()
    framework = ask_framework()
    design = ask_design()
    tools = ask_tools()
     # TODO return TemplateConfig object


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

