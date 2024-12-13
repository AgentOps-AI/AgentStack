"""
This it the beginning of the agentstack public API. 

Methods that have been imported into this file are expected to be used by the
end user inside of their project. 
"""
from pathlib import Path
from agentstack import conf
from agentstack.inputs import get_inputs

___all___ = [
    "conf", 
    "get_tags", 
    "get_inputs", 
]


def get_tags() -> list[str]:
    """
    Get a list of tags relevant to the user's project.
    """
    return ['agentstack', conf.get_framework(), *conf.get_installed_tools()]

