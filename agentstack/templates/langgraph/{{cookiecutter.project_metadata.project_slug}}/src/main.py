#!/usr/bin/env python
import sys
from graph import {{cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize}}Graph
import agentstack
import agentops

agentops.init(default_tags=agentstack.get_tags())

instance = {{cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize}}Graph()

def run():
    """
    Run the agent.
    """
    instance.run(inputs=agentstack.get_inputs())


if __name__ == '__main__':
    run()