from typing import Optional
import itertools
import inquirer
from agentstack.utils import term_color
from agentstack import generation
from agentstack._tools import get_all_tools
from agentstack.agents import get_all_agents


def list_tools():
    """
    List all available tools by category.
    """
    tools = get_all_tools()
    categories = {}
    
    # Group tools by category
    for tool in tools:
        if tool.category not in categories:
            categories[tool.category] = []
        categories[tool.category].append(tool)
    
    print("\n\nAvailable AgentStack Tools:")
    # Display tools by category
    for category in sorted(categories.keys()):
        print(f"\n{category}:")
        for tool in categories[category]:
            print("  - ", end='')
            print(term_color(f"{tool.name}", 'blue'), end='')
            print(f": {tool.url if tool.url else 'AgentStack default tool'}")

    print("\n\n✨ Add a tool with: agentstack tools add <tool_name>")
    print("   https://docs.agentstack.sh/tools/core")


def add_tool(tool_name: Optional[str], agents=Optional[list[str]]):
    """
    Add a tool to the user's project.
    If no tool name is provided:
        - prompt the user to select a tool
        - prompt the user to select one or more agents
    If a tool name is provided:
        - add the tool to the user's project
        - add the tool to the specified agents or all agents if none are specified
    """
    if not tool_name:
        # ask the user for the tool name
        tools_list = [
            inquirer.List(
                "tool_name",
                message="Select a tool to add to your project",
                choices=[tool.name for tool in get_all_tools()],
            )
        ]
        try:
            tool_name = inquirer.prompt(tools_list)['tool_name']
        except TypeError:
            return  # user cancelled the prompt

        # ask the user for the agents to add the tool to
        agents_list = [
            inquirer.Checkbox(
                "agents",
                message="Select which agents to make the tool available to",
                choices=[agent.name for agent in get_all_agents()],
            )
        ]
        try:
            agents = inquirer.prompt(agents_list)['agents']
        except TypeError:
            return  # user cancelled the prompt

    assert tool_name  # appease type checker
    generation.add_tool(tool_name, agents=agents)
