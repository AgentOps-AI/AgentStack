import asyncio
import json
import os
import tempfile
import time
import tomllib
import webbrowser
import zipfile
from pathlib import Path

from agentstack.auth import get_stored_token, login
from agentstack.cli.spinner import Spinner
from agentstack.conf import ConfigFile
from agentstack.utils import term_color
from agentstack import log
import requests
import websockets


async def connect_websocket(project_id, spinner):
    uri = f"ws://localhost:3000/ws/build/{project_id}"
    async with websockets.connect(uri) as websocket:
        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                if data['type'] == 'build':
                    spinner.clear_and_log(f"🏗️  {data.get('data','')}", 'info')
                elif data['type'] == 'push':
                    spinner.clear_and_log(f"📤 {data.get('data','')}", 'info')
                elif data['type'] == 'connected':
                    spinner.clear_and_log(f"\n\n~~ Build stream connected! ~~")
                elif data['type'] == 'error':
                    raise Exception(f"Failed to deploy: {data.get('data')}")
        except websockets.ConnectionClosed:
            raise Exception("Websocket connection closed unexpectedly")


async def deploy():
    log.info("Deploying your agentstack agent!")
    bearer_token = get_stored_token()
    if not bearer_token:
        success = login()
        if success:
            bearer_token = get_stored_token()
        else:
            log.error(term_color("Failed to authenticate with AgentStack.sh", "red"))
            return

    project_id = get_project_id()

    with Spinner() as spinner:
        websocket_task = asyncio.create_task(connect_websocket(project_id, spinner))
        time.sleep(0.1)
        try:
            spinner.update_message("Collecting files")
            spinner.clear_and_log("  🗄️ Files collected")
            files = collect_files(str(Path('.')), ('.py', '.toml', '.yaml', '.json'))
            if not files:
                raise Exception("No files found to deploy")

            spinner.update_message("Creating zip file")
            zip_file = create_zip_in_memory(files, spinner)
            spinner.clear_and_log("  🗜️ Created zip file")

            spinner.update_message("Uploading to server")

            response = requests.post(
                'http://localhost:3000/deploy/build',
                files={'code': ('code.zip', zip_file)},
                params={'projectId': project_id},
                headers={'Authorization': f'Bearer {bearer_token}'}
            )

            spinner.clear_and_log("  📡  Uploaded to server")

            if response.status_code != 200:
                raise Exception(response.text)

            spinner.update_message("Building your agent")

            # Wait for build completion
            await websocket_task

            log.success("\n🚀 Successfully deployed with AgentStack.sh! Opening in browser...")
            # webbrowser.open(f"http://localhost:5173/project/{project_id}")

        except Exception as e:
            spinner.stop()
            log.error(f"\n🙃 Failed to deploy with AgentStack.sh: {e}")
            return

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
    log.info("🚧 Creating AgentStack.sh Project")
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
        log.error(f"Error making request: {e}")
        return None


def collect_files(root_path='.', file_types=('.py', '.toml', '.yaml', '.json')):
    """Collect files of specified types from directory tree."""
    files = set()  # Using set for faster lookups and unique entries
    root = Path(root_path)

    def should_process_dir(path):
        """Check if directory should be processed."""
        skip_dirs = {'.git', '.venv', 'venv', '__pycache__', 'node_modules', '.pytest_cache'}
        return path.name not in skip_dirs

    def process_directory(path):
        """Process a directory and collect matching files."""
        if not should_process_dir(path):
            return set()

        matching_files = set()
        try:
            for file_path in path.iterdir():
                if file_path.is_file() and file_path.suffix in file_types:
                    matching_files.add(file_path)
                elif file_path.is_dir():
                    matching_files.update(process_directory(file_path))
        except PermissionError:
            log.error(f"Permission denied accessing {path}")
        except Exception as e:
            log.error(f"Error processing {path}: {e}")

        return matching_files

    # Start with files in root directory
    files.update(f for f in root.iterdir() if f.is_file() and f.suffix in file_types)

    # Process subdirectories
    for path in root.iterdir():
        if path.is_dir():
            files.update(process_directory(path))

    return sorted(files)  # Convert back to sorted list for consistent ordering


def create_zip_in_memory(files, spinner):
    """Create a ZIP file in memory with progress updates."""
    tmp = tempfile.SpooledTemporaryFile(max_size=10 * 1024 * 1024)
    total_files = len(files)

    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, file in enumerate(files, 1):
            try:
                spinner.update_message(f"Adding files to zip ({i}/{total_files})")
                zf.write(file)
            except Exception as e:
                log.error(f"Error adding {file} to zip: {e}")

    tmp.seek(0)

    # Get final zip size
    current_pos = tmp.tell()
    tmp.seek(0, 2)  # Seek to end
    zip_size = tmp.tell()
    tmp.seek(current_pos)  # Restore position

    def format_size(size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024 or unit == 'GB':
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024

    # log.info(f"    > Zip created: {format_size(zip_size)}")

    return tmp