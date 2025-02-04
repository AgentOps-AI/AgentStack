#!/usr/bin/env python
import agentstack
import agentops
from stack import {{cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize}}Stack


agentops.init(default_tags=agentstack.get_tags())

instance = {{cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize}}Stack()

def run():
    """
    Run the agent.
    """
    instance.run(inputs=agentstack.get_inputs())
    agentops.end_session(end_state='Success')

if __name__ == '__main__':
    run()