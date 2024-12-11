#!/usr/bin/env python
import json
import sys
from typing import Optional

from crew import WebresearcherCrew
import agentops
from dotenv import load_dotenv
load_dotenv()

agentops.init(default_tags=['web_researcher', 'agentstack'])


def run(inputs: Optional[dict] = None):
    """
    Run the crew.
    """

    print(inputs)

    if not inputs:
        inputs = {
            'url': 'https://github.com/AgentOps-AI/AgentStack/tree/main'
        }
    return WebresearcherCrew().crew().kickoff(inputs=inputs)


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs"
    }
    try:
        WebresearcherCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        WebresearcherCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs"
    }
    try:
        WebresearcherCrew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


if __name__ == '__main__':
    data = None
    if len(sys.argv) > 1:
        data_str = sys.argv[1]
        data = json.loads(data_str)
    run(data)