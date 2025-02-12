#!/usr/bin/env python
import sys
from crew import {{cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize}}Crew
import agentstack
import agentops

agentops.init(default_tags=agentstack.get_tags(), skip_auto_end_session=True, auto_start_session=False)

instance = {{cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize}}Crew().crew()

def run() -> [str, str]:
    """
    Run the agent.
    Returns:
        A Tuple: (The output of running the agent, agentops session_id)
    """
    session = agentops.start_session()
    try:
        result = instance.kickoff(inputs=agentstack.get_inputs())
        session.end_session(end_state="Success")
        return result.raw, str(session.session_id)
    except:
        session.end_session(end_state="Fail")


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