import os, sys
from typing import Optional

from agentstack import conf
from agentstack.conf import ConfigFile
from agentstack.exceptions import ValidationError
from agentstack import frameworks
from agentstack import packaging
from agentstack.utils import term_color
from agentstack._tools import ToolConfig
from agentstack.generation.files import EnvFile


def add_tool(tool_name: str, agents: Optional[list[str]] = []):
    agentstack_config = ConfigFile()
    tool = ToolConfig.from_tool_name(tool_name)

    if tool_name in agentstack_config.tools:
        print(term_color(f'Tool {tool_name} is already installed', 'blue'))
    else:  # handle install
        if tool.dependencies:
            packaging.install(' '.join(tool.dependencies))

        if tool.env:  # add environment variables which don't exist
            with EnvFile() as env:
                for var, value in tool.env.items():
                    env.append_if_new(var, value)
            with EnvFile(".env.example") as env:
                for var, value in tool.env.items():
                    env.append_if_new(var, value)

        if tool.post_install:
            os.system(tool.post_install)

        with agentstack_config as config:
            config.tools.append(tool.name)

    # Edit the framework entrypoint file to include the tool in the agent definition
    if not agents:  # If no agents are specified, add the tool to all agents
        agents = frameworks.get_agent_names()
    for agent_name in agents:
        print(f'Adding tool {tool.name} to agent {agent_name}')
        frameworks.add_tool(tool, agent_name)

    print(term_color(f'🔨 Tool {tool.name} added to agentstack project successfully', 'green'))
    if tool.cta:
        print(term_color(f'🪩  {tool.cta}', 'blue'))


def remove_tool(tool_name: str, agents: Optional[list[str]] = []):
    agentstack_config = ConfigFile()

    if tool_name not in agentstack_config.tools:
        print(term_color(f'Tool {tool_name} is not installed', 'red'))
        sys.exit(1)

    # TODO ensure other agents are not using the tool
    tool = ToolConfig.from_tool_name(tool_name)
    if tool.dependencies:
        # TODO split on "==", ">=", etc. and only remove by package name
        packaging.remove(' '.join(tool.dependencies))

    # Edit the framework entrypoint file to exclude the tool in the agent definition
    if not agents:  # If no agents are specified, remove the tool from all agents
        agents = frameworks.get_agent_names()
    for agent_name in agents:
        frameworks.remove_tool(tool, agent_name)

    if tool.post_remove:
        os.system(tool.post_remove)
    # We don't remove the .env variables to preserve user data.

    with agentstack_config as config:
        config.tools.remove(tool.name)

    print(
        term_color(f'🔨 Tool {tool_name}', 'green'),
        term_color('removed', 'red'),
        term_color('from agentstack project successfully', 'green'),
    )
