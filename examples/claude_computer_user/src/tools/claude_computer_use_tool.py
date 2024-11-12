from crewai_tools import tool
from dotenv import load_dotenv
import os
import subprocess
import json
import time
import requests

load_dotenv()

api_key = os.getenv('CLAUDE_API_KEY')

def check_docker_running():
    """Check if Docker daemon is running."""
    try:
        subprocess.run(['docker', 'info'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_container_exists(container_name):
    """Check if a container with the given name already exists."""
    try:
        result = subprocess.run(
            ['docker', 'ps', '-a', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            check=True
        )
        return container_name in result.stdout.split('\n')
    except subprocess.CalledProcessError:
        return False

def check_container_status(container_name):
    """Check if container is running and service is responding."""
    try:
        # Check if container is running
        result = subprocess.run(
            ['docker', 'inspect', '--format', '{{.State.Running}}', container_name],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip() != 'true':
            return False
        
        # Check if service is responding
        try:
            response = requests.get('http://localhost:8080', timeout=1)
            return response.status_code == 200
        except requests.RequestException:
            return False
            
    except subprocess.CalledProcessError:
        return False

def wait_for_service_ready(container_name, timeout=60):
    """Wait for the service to be ready with timeout."""
    print(f"Waiting for {container_name} to be ready...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        if check_container_status(container_name):
            return True
        time.sleep(2)
        print(".", end="", flush=True)
    print("\nTimeout reached")
    return False

@tool("Start claude computer use")
def start_claude_computer_use():
    """
    Tool to run Claude computer use using Claude's docker image
    """
    container_name = "claude-computer-use"
    
    if not check_docker_running():
        print("Docker daemon is not running")
        return False
        
    if check_container_exists(container_name):
        try:
            print(f"Removing existing container '{container_name}'...")
            subprocess.run(['docker', 'rm', '-f', container_name], 
                         check=True, 
                         capture_output=True)
        except subprocess.CalledProcessError:
            print(f"Failed to remove existing container '{container_name}'")
            return False
    
    docker_cmd = [
        'docker', 'run',
        '--name', container_name,
        '-e', f'ANTHROPIC_API_KEY={api_key}',
        '-v', f'{os.path.expanduser("~")}/.anthropic:/home/computeruse/.anthropic',
        '-p', '5900:5900',
        '-p', '8501:8501',
        '-p', '6080:6080',
        '-p', '8080:8080',
        '-d',  # Run in detached mode
        'ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest'
    ]
    
    try:
        print("Starting container...")
        subprocess.run(docker_cmd, check=True, capture_output=True)
        
        # Wait for container to be ready
        if wait_for_service_ready(container_name):
            print("\nContainer is ready! Access Claude at http://localhost:8080")
            return True
            
        # If we get here, service didn't come up in time
        print("\nContainer started but service is not responding")
        return False
            
    except subprocess.CalledProcessError as e:
        print(f"Failed to start container: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    start_claude_computer_use()