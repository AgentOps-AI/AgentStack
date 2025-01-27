from typing import Optional
import itertools
import inquirer
from agentstack.utils import term_color
from agentstack import generation
from agentstack._tools import get_all_tools
from agentstack.agents import get_all_agents
from pathlib import Path
import sys
import json


def list_tools():
    """
    List all available tools by category.
    """
    tools = [t for t in get_all_tools() if t is not None]  # Filter out None values
    categories = {}
    custom_tools = []
    
    # Group tools by category
    for tool in tools:
        if tool.category == 'custom':
            custom_tools.append(tool)
        else:
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

    # Display custom tools if any exist
    if custom_tools:
        print("\nCustom Tools:")
        for tool in custom_tools:
            print("  - ", end='')
            print(term_color(f"{tool.name}", 'blue'), end='')
            print(": Custom tool")

    print("\n\n✨ Add a tool with: agentstack tools add <tool_name>")
    print("   Create a custom tool with: agentstack tools create <tool_name>")
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
        # Get all available tools including custom ones
        available_tools = [t for t in get_all_tools() if t is not None]
        tool_names = [t.name for t in available_tools]
        
        # ask the user for the tool name
        tools_list = [
            inquirer.List(
                "tool_name",
                message="Select a tool to add to your project",
                choices=tool_names,
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


def create_tool(tool_name: str):
    """Create a new custom tool.
    
    Args:
        tool_name: Name of the tool to create (must be snake_case)
    """
    # Check if tool already exists
    user_tools_dir = Path('src/tools').resolve()
    tool_path = user_tools_dir / tool_name
    if tool_path.exists():
        print(term_color(f"Tool '{tool_name}' already exists.", 'yellow'))
        sys.exit(1)

    # Create tool directory
    tool_path.mkdir(parents=True, exist_ok=False)

    # Create __init__.py with basic function template
    init_file = tool_path / '__init__.py'
    init_content = f'''def define_your_tool():
    """
    Define your tool's functionality here.
    """
    pass
'''
    init_file.write_text(init_content)

    # Create config.json with basic structure
    config = {
        "name": tool_name,
        "category": "custom",
        "tools": ["define_your_tool"],
        "url": "",
        "cta": "",
        "env": {},
        "dependencies": [],
        "post_install": "",
        "post_remove": ""
    }
    config_file = tool_path / 'config.json'
    config_file.write_text(json.dumps(config, indent=4))

    print(term_color(f"Tool '{tool_name}' has been created successfully in {user_tools_dir}.", 'green'))
