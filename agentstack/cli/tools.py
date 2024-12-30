from typing import Optional
import itertools
import sys
import inquirer
from agentstack.utils import term_color
from agentstack import generation
from agentstack.tools import get_all_tools
from agentstack.agents import get_all_agents
from agentstack.exceptions import ToolError, ValidationError


def list_tools():
    """
    List all available tools by category.
    """
    try:
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
    except ToolError:
        print(term_color("Could not retrieve list of tools. The tools directory may be corrupted or missing.", 'red'))
        sys.exit(1)
    except ValidationError as e:
        print(term_color(f"Validation error: {str(e)}", 'red'))
        sys.exit(1)
    except Exception:
        print(term_color("An unexpected error occurred while listing tools.", 'red'))
        sys.exit(1)


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
    try:
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
    except ToolError:
        print(term_color(f"Could not add tool '{tool_name}'. Run 'agentstack tools list' to see available tools.", 'red'))
        sys.exit(1)
    except ValidationError as e:
        print(term_color(f"Validation error: {str(e)}", 'red'))
        sys.exit(1)
    except Exception:
        print(term_color("An unexpected error occurred while adding the tool.", 'red'))
        sys.exit(1)


def remove_tool(tool_name: str, agents: Optional[list[str]] = []):
    """Remove a tool from the project"""
    try:
        generation.remove_tool(tool_name, agents=agents)
    except ToolError as e:
        if "not installed" in str(e):
            print(term_color(f"Tool '{tool_name}' is not installed in this project.", 'red'))
        else:
            print(term_color(f"Could not remove tool '{tool_name}'. The tool may be in use or corrupted.", 'red'))
        sys.exit(1)
    except ValidationError as e:
        print(term_color(f"Validation error: {str(e)}", 'red'))
        sys.exit(1)
    except Exception:
        print(term_color("An unexpected error occurred while removing the tool.", 'red'))
        sys.exit(1)
