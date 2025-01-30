import os, sys
from typing import Optional
from agentstack import conf, log
from agentstack.conf import ConfigFile
from agentstack.exceptions import ValidationError
from agentstack import frameworks
from agentstack import packaging
from agentstack.utils import term_color
from agentstack._tools import ToolConfig
from agentstack.generation import asttools
from agentstack.generation.files import EnvFile


def add_tool(name: str, agents: Optional[list[str]] = []):
    agentstack_config = ConfigFile()
    tool = ToolConfig.from_tool_name(name)

    if name in agentstack_config.tools:
        log.notify(f'Tool {name} is already installed')
    else:  # handle install
        if tool.dependencies:
            for dependency in tool.dependencies:
                packaging.install(dependency)

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
        agents = frameworks.get_agent_method_names()
    for agent_name in agents:
        frameworks.add_tool(tool, agent_name)

    log.success(f'🔨 Tool {tool.name} added to agentstack project successfully!')
    if tool.cta:
        log.notify(f'🪩  {tool.cta}')


def remove_tool(name: str, agents: Optional[list[str]] = []):
    agentstack_config = ConfigFile()

    if name not in agentstack_config.tools:
        raise ValidationError(f'Tool {name} is not installed')

    # TODO ensure other agents are not using the tool
    tool = ToolConfig.from_tool_name(name)
    if tool.dependencies:
        for dependency in tool.dependencies:
            packaging.remove(dependency)

    # Edit the framework entrypoint file to exclude the tool in the agent definition
    if not agents:  # If no agents are specified, remove the tool from all agents
        agents = frameworks.get_agent_method_names()
    for agent_name in agents:
        frameworks.remove_tool(tool, agent_name)

    if tool.post_remove:
        os.system(tool.post_remove)
    # We don't remove the .env variables to preserve user data.

    with agentstack_config as config:
        config.tools.remove(tool.name)

    log.success(f'🔨 Tool {tool.name} removed from agentstack project successfully')
