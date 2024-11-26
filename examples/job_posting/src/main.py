#!/usr/bin/env python
import sys
from crew import JobpostingCrew
import agentops
from dotenv import load_dotenv
load_dotenv()

agentops.init()

inputs = {
        'company_domain': 'https://agen.cy',
        'company_description': "From open source AI agent developer tools like AgentOps to Fortune 500 enterprises, we help clients create safe, reliable, and scalable AI agents.",
        'hiring_needs': 'Infrastructure engineer for deploying AI agents at scale',
        'specific_benefits': 'Daily lunch',
    }

def run():
    """
    Run the crew.
    """
    JobpostingCrew().crew().kickoff(inputs=inputs)


def train():
    """
    Train the crew for a given number of iterations.
    """
    try:
        JobpostingCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        JobpostingCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    try:
        JobpostingCrew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


if __name__ == '__main__':
    run()