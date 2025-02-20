from typing import Optional
import os
import time
import questionary
from questionary import Choice
from art import text2art
from agentstack import log
from agentstack.frameworks import SUPPORTED_FRAMEWORKS
from agentstack.utils import is_snake_case
from agentstack.cli import welcome_message
from agentstack._tools import get_all_tools
from agentstack.templates import TemplateConfig
from agentstack.providers import get_available_models


class WizardData(dict):
    def to_template_config(self) -> TemplateConfig:
        agents = []
        for agent in self['design']['agents']:
            agents.append(
                TemplateConfig.Agent(
                    **{
                        'name': agent['name'],
                        'role': agent['role'],
                        'goal': agent['goal'],
                        'backstory': agent['backstory'],
                        'llm': agent['model'],
                    }
                )
            )

        tasks = []
        for task in self['design']['tasks']:
            tasks.append(
                TemplateConfig.Task(
                    **{
                        'name': task['name'],
                        'description': task['description'],
                        'expected_output': task['expected_output'],
                        'agent': task['agent'],
                    }
                )
            )

        tools = []
        for tool in self['tools']:
            tools.append(
                TemplateConfig.Tool(
                    **{
                        'name': tool,
                        'agents': [agent.name for agent in agents],
                    }
                )
            )

        return TemplateConfig(
            name=self['project']['name'],
            description=self['project']['description'],
            template_version=4,
            framework=self['framework'],
            method='sequential',
            manager_agent=None,
            agents=agents,
            tasks=tasks,
            tools=tools,
            graph=[],
            inputs={},
        )


def ask_framework() -> str:
    return questionary.select(
        "What agent framework do you want to use?",
        choices=SUPPORTED_FRAMEWORKS,
        use_indicator=True,
    ).ask()


def ask_agent_details():
    agent = {}

    while True:
        name = questionary.text(
            "What's the name of this agent? (snake_case)",
            validate=lambda text: len(text) >= 3 and is_snake_case(text),
        ).ask()
        if name:
            break
    agent['name'] = name

    agent['role'] = questionary.text(
        "What role does this agent have?", validate=lambda text: len(text) >= 3
    ).ask()

    agent['goal'] = questionary.text(
        "What is the goal of the agent?", validate=lambda text: len(text) >= 10
    ).ask()

    agent['backstory'] = questionary.text(
        "Give your agent a backstory", validate=lambda text: len(text) >= 10
    ).ask()

    available_models = get_available_models()
    agent['model'] = questionary.select(
        "What LLM should this agent use?",
        choices=available_models,
        default=available_models[0] if available_models else None,
        use_indicator=True,
        use_shortcuts=False,
        use_jk_keys=False,
        use_emacs_keys=False,
        use_arrow_keys=True,
        use_search_filter=True,
    ).ask()

    return agent


def ask_task_details(agents: list[dict]) -> dict:
    task = {}

    while True:
        name = questionary.text(
            "What's the name of this task? (snake_case)",
            validate=lambda text: len(text) >= 3 and is_snake_case(text),
        ).ask()
        if name:
            break
    task['name'] = name

    task['description'] = questionary.text(
        "Describe the task in more detail", validate=lambda text: len(text) >= 10
    ).ask()

    task['expected_output'] = questionary.text(
        "What do you expect the result to look like? (ex: A 5 bullet point summary of the email)",
        validate=lambda text: len(text) >= 10,
    ).ask()

    task['agent'] = questionary.select(
        "Which agent should be assigned this task?",
        choices=[a['name'] for a in agents],
        use_indicator=True,
        use_shortcuts=False,
        use_jk_keys=False,
        use_emacs_keys=False,
        use_arrow_keys=True,
        use_search_filter=True,
    ).ask()

    return task


def ask_design() -> dict:
    use_wizard = questionary.confirm(
        "Would you like to use the CLI wizard to set up agents and tasks?",
    ).ask()

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
        make_agent = questionary.confirm(message="Create another agent?").ask()

    print('')
    for x in range(3):
        time.sleep(0.3)
        print('.')
    # fmt: off
    # most formatters wanna make changes to the ’ character.
    print('Boom! We made some agents (ﾉ>ω<)ﾉ :｡･:*:･ﾟ’★,｡･:*:･ﾟ’☆')
    # fmt: on
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
        make_task = questionary.confirm(message="Create another task?").ask()

    print('')
    for x in range(3):
        time.sleep(0.3)
        print('.')
    print('Let there be tasks (ノ ˘_˘)ノ　ζ|||ζ　ζ|||ζ　ζ|||ζ')

    return {'tasks': tasks, 'agents': agents}


def ask_tools() -> list:
    use_tools = questionary.confirm(
        "Do you want to add agent tools now? (you can do this later with `agentstack tools add <tool_name>`)",
    ).ask()

    if not use_tools:
        return []

    tools_to_add = []
    tool_configs = get_all_tools()

    while True:
        tool_categories = list(set(t.category for t in tool_configs))

        tool_type = questionary.select(
            "What category tool do you want to add?",
            choices=tool_categories + ["~~ Stop adding tools ~~"],
            use_indicator=True,
            use_shortcuts=False,
            use_jk_keys=False,
            use_emacs_keys=False,
            use_arrow_keys=True,
            use_search_filter=True,
        ).ask()

        if tool_type == "~~ Stop adding tools ~~":
            break

        tools_in_cat = [t for t in tool_configs if t.category == tool_type]

        tool_selection = questionary.select(
            "Select your tool",
            choices=[
                Choice(f"{t.name} - {t.url}", disabled="Already added" if t in tools_to_add else None)
                for t in tools_in_cat
            ],
            use_indicator=True,
            use_shortcuts=False,
            use_jk_keys=False,
            use_emacs_keys=False,
            use_arrow_keys=True,
            use_search_filter=True,
        ).ask()

        tool_name = tool_selection.split(' - ')[0]
        tools_to_add.append(tool_name)

        log.info("Adding tools:")
        for t in tools_to_add:
            log.info(f'  - {t}')
        log.info('')

        if not questionary.confirm("Add another tool?").ask():
            break

    return tools_to_add


def ask_project_details(slug_name: Optional[str] = None) -> dict:
    while True:
        name = questionary.text("What's the name of your project (snake_case)", default=slug_name or '').ask()

        if is_snake_case(name):
            break
        log.error("Project name must be snake case")

    questions = [
        {'type': 'text', 'name': 'version', 'message': "What's the initial version", 'default': '0.1.0'},
        {'type': 'text', 'name': 'description', 'message': 'Enter a description for your project'},
        {'type': 'text', 'name': 'author', 'message': "Who's the author (your name)?"},
    ]

    answers = questionary.prompt(questions)
    answers['name'] = name
    return answers


def run_wizard(slug_name: str) -> TemplateConfig:
    project_details = ask_project_details(slug_name)
    welcome_message()
    framework = ask_framework()
    design = ask_design()
    tools = ask_tools()

    wizard_data = WizardData(
        {
            'project': project_details,
            'framework': framework,
            'design': design,
            'tools': tools,
        }
    )
    return wizard_data.to_template_config()
