"""
This it the beginning of the agentstack public API. 

Methods that have been imported into this file are expected to be used by the
end user inside of their project. 
"""
from pathlib import Path
from agentstack import conf
from agentstack.utils import get_framework
from agentstack.agents import get_agent
from agentstack.tasks import get_task
from agentstack.inputs import get_inputs

___all___ = [
    "conf", 
    "agent", 
    "task", 
    "get_tags", 
    "get_framework", 
    "get_agent", 
    "get_task", 
    "get_inputs", 
]

def agent():
    """
    The `agent` decorator is used to mark a method that implements an Agent. 
    """
    pass


def task():
    """
    The `task` decorator is used to mark a method that implements a Task.
    """
    pass


def get_tags() -> list[str]:
    """
    Get a list of tags relevant to the user's project.
    """
    return ['agentstack', get_framework(), *conf.get_installed_tools()]

