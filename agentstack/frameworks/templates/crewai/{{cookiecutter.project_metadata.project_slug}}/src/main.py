#!/usr/bin/env python
import sys
from crew import {{cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize}}Crew
import agentstack
import agentops

agentops.init(default_tags=agentstack.get_tags())

instance = {{cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize}}Crew().crew()

def run():
    """
    Run the agent.
    """
    instance.kickoff(inputs=agentstack.get_inputs())


def train():
    """
    Train the crew for a given number of iterations.
    """
    try:
        instance.train(
            n_iterations=int(sys.argv[1]), 
            filename=sys.argv[2], 
            inputs=agentstack.get_inputs(), 
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        instance.replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    try:
        instance.test(
            n_iterations=int(sys.argv[1]), 
            openai_model_name=sys.argv[2], 
            inputs=agentstack.get_inputs(), 
        )
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


if __name__ == '__main__':
    run()