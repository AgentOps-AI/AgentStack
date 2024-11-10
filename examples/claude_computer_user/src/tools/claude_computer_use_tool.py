from crewai_tools import tool
from dotenv import load_dotenv
import os
import subprocess

load_dotenv()

api_key = os.getenv('CLAUDE_API_KEY')

@tool("Start claude computer use")
def start_claude_computer_use():
    """
    Tool to run Claude computer use using Claude's docker image
    """
    
    # Docker command as a list of arguments
    docker_cmd = [
        'docker', 'run',
        '-e', f'ANTHROPIC_API_KEY={api_key}',
        '-v', f'{os.path.expanduser("~")}/.anthropic:/home/computeruse/.anthropic',
        '-p', '5900:5900',
        '-p', '8501:8501',
        '-p', '6080:6080',
        '-p', '8080:8080',
        '-it', 'ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest'
    ]
    
    try:
        # Run docker command
        subprocess.run(docker_cmd, check=True)
        print('Running docker')
    except subprocess.CalledProcessError as e:
        print(f'Error running docker: {e}')
    except Exception as e:
        print(f'Unexpected error: {e}')