import os
import tempfile
import tomllib
import webbrowser
import zipfile
from pathlib import Path

from agentstack.auth import get_stored_token, login
from agentstack.conf import ConfigFile
from agentstack.utils import term_color
import requests


def deploy():
    bearer_token = get_stored_token()
    if not bearer_token:
        success = login()
        if success:
            bearer_token = get_stored_token()
        else:
            print(term_color("Failed to authenticate with AgentStack.sh", "red"))
            return

    project_id = get_project_id()
    pyproject = load_pyproject()
    files = list(Path('.').rglob('*.py'))

    with tempfile.NamedTemporaryFile(suffix='.zip') as tmp:
        with zipfile.ZipFile(tmp.name, 'w') as zf:
            for file in files:
                zf.write(file)
            if pyproject:
                zf.write("pyproject.toml")

        response = requests.post(
            'http://localhost:3000/deploy/build',
            files={'code': ('code.zip', open(tmp.name, 'rb'))},
            params={'projectId': project_id},
            headers={'Authorization': f'Bearer {bearer_token}'}
        )

    if response.status_code != 200:
        print(term_color("Failed to deploy with AgentStack.sh", "red"))
        print(response.text)
        return

    print(term_color("🚀 Successfully deployed with AgentStack.sh! Opening in browser...", "green"))
    webbrowser.open(f"http://localhost:5173/project/{project_id}")


def load_pyproject():
   if os.path.exists("pyproject.toml"):
       with open("pyproject.toml", "rb") as f:
           return tomllib.load(f)
   return None

def get_project_id():
    project_config = ConfigFile()
    project_id = project_config.hosted_project_id

    if project_id:
        return project_id

    bearer_token = get_stored_token()

    # if not in config, create project and store it
    print(term_color("🚧 Creating AgentStack.sh Project", "green"))
    headers = {
        'Authorization': f'Bearer {bearer_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'name': project_config.project_name
    }

    try:
        response = requests.post(
            url="http://localhost:3000/projects",
            # url="https://api.agentstack.sh/projects",
            headers=headers,
            json=payload
        )

        response.raise_for_status()
        res_data = response.json()
        project_id = res_data['id']
        project_config.hosted_project_id = project_id
        project_config.write()
        return project_id

    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

