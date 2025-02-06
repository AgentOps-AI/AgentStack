from typing import Optional
import os
import time
import inquirer
import webbrowser
from art import text2art
from agentstack import log
from agentstack.frameworks import SUPPORTED_FRAMEWORKS
from agentstack.utils import open_json_file, is_snake_case
from agentstack.cli import welcome_message, get_validated_input
from agentstack.cli.cli import PREFERRED_MODELS
from agentstack._tools import get_all_tools, get_all_tool_names
from agentstack.templates import TemplateConfig


class WizardData(dict):
    def to_template_config(self) -> TemplateConfig:
        agents = []
        for agent in self['design']['agents']:
            agents.append(TemplateConfig.Agent(**{
                'name': agent['name'],
                'role': agent['role'],
                'goal': agent['goal'],
                'backstory': agent['backstory'],
                'llm': agent['model'],
            }))
        
        tasks = []
        for task in self['design']['tasks']:
            tasks.append(TemplateConfig.Task(**{
                'name': task['name'],
                'description': task['description'],
                'expected_output': task['expected_output'],
                'agent': task['agent'],
            }))
        
        tools = []
        for tool in self['tools']:
            tools.append(TemplateConfig.Tool(**{
                'name': tool,
                'agents': [agent.name for agent in agents],  # all agents
            }))
        
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


def run_wizard(slug_name: str) -> TemplateConfig:
    project_details = ask_project_details(slug_name)
    welcome_message()
    framework = ask_framework()
    design = ask_design()
    tools = ask_tools()
    
    wizard_data = WizardData({
        'project': project_details,
        'framework': framework,
        'design': design,
        'tools': tools,
    })
    return wizard_data.to_template_config()


def ask_framework() -> str:
    framework = inquirer.list_input(
        message="What agent framework do you want to use?",
        choices=SUPPORTED_FRAMEWORKS,
    )
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

    #log.success("Congrats! Your project is ready to go! Quickly add features now or skip to do it later.\n\n")
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
    tool_configs = get_all_tools()

    while adding_tools:
        tool_categories = []
        for tool_config in tool_configs:
            if tool_config.category not in tool_categories:
                tool_categories.append(tool_config.category)
        
        tool_type = inquirer.list_input(
            message="What category tool do you want to add?",
            choices=tool_categories + ["~~ Stop adding tools ~~"],
        )

        tools_in_cat = []
        for tool_config in tool_configs:
            if tool_config.category == tool_type:
                tools_in_cat.append(tool_config)
        
        tool_selection = inquirer.list_input(
            message="Select your tool", 
            choices=[f"{t.name} - {t.url}" for t in tools_in_cat if t not in tools_to_add], 
        )

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

