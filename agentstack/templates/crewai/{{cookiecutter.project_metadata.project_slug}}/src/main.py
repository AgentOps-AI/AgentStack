#!/usr/bin/env python
import sys
from crew import {{cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize}}Crew
import agentops
from dotenv import load_dotenv
load_dotenv()

agentops.init()


def run():
    """
    Run the crew.
    """
    inputs = {
{%- for input in cookiecutter.structure.inputs %}
        "{{input}}": "",
{%- endfor %}
    }
    {{cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize}}Crew().crew().kickoff(inputs=inputs)


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
{%- for input in cookiecutter.structure.inputs %}
        "{{input}}": "",
{%- endfor %}
    }
    try:
        {{cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize}}Crew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        {{cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize}}Crew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
{%- for input in cookiecutter.structure.inputs %}
        "{{input}}": "",
{%- endfor %}
    }
    try:
        {{cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize}}Crew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


if __name__ == '__main__':
    run()