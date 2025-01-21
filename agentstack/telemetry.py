# hi :)
#
# if you're reading this, you probably saw "telemetry.py" and
# got mad and went to go see how we're spying on you
#
# i really hate to put this functionality in and was very
# resistant to it. as a human, i value privacy as a fundamental
# human right. but i also value what we're building.
#
# i have strong conviction for what AgentStack is and will be.
# it's showing some great progress, but for us to know how to
# build it best, i need to know if and how people are using it
#
# if you want to opt-out of telemetry, you can add the following
# configuration to your agentstack.json file:
#
# telemetry_opt_out: false
#
# i'm a single developer with a passion, working to lower the barrier
# of entry to building and deploying agents. it would be really
# cool of you to allow telemetry <3
#
# - braelyn
import json
import os
import platform
import socket
import uuid
from pathlib import Path
from typing import Optional
import psutil
import requests
from agentstack import conf
from agentstack.auth import get_stored_token
from agentstack.utils import get_telemetry_opt_out, get_framework, get_version, get_base_dir

TELEMETRY_URL = 'https://api.agentstack.sh/telemetry'
USER_GUID_FILE_PATH = get_base_dir() / ".cli-user-guid"


def collect_machine_telemetry(command: str):
    if command != "init" and get_telemetry_opt_out():
        return

    telemetry_data = {
        'os': platform.system(),
        'hostname': socket.gethostname(),
        'platform': platform.platform(),
        'os_version': platform.version(),
        'cpu_count': psutil.cpu_count(logical=True),
        'memory': psutil.virtual_memory().total,
        'agentstack_version': get_version(),
        'cli_user_id': _get_cli_user_guid()
    }

    if command != "init":
        telemetry_data['framework'] = conf.get_framework()
    else:
        telemetry_data['framework'] = "n/a"

    if telemetry_data['framework'] is None:
        telemetry_data['framework'] = "n/a"

    # Attempt to get general location based on public IP
    try:
        response = requests.get('https://ipinfo.io/json')
        if response.status_code == 200:
            location_data = response.json()
            telemetry_data.update(
                {
                    'ip': location_data.get('ip'),
                    'city': location_data.get('city'),
                    'region': location_data.get('region'),
                    'country': location_data.get('country'),
                }
            )
    except requests.RequestException as e:
        telemetry_data['location_error'] = str(e)

    return telemetry_data


def track_cli_command(command: str, args: Optional[str] = None):
    if bool(os.getenv('AGENTSTACK_IS_TEST_ENV')):
        return

    try:
        data = collect_machine_telemetry(command)
        headers = {}
        token = get_stored_token()
        if token:
            headers['Authorization'] = f'Bearer {token}'

        return requests.post(TELEMETRY_URL, json={"command": command, "args":args, **data}, headers=headers).json().get('id')
    except Exception:
        pass

def update_telemetry(id: int, result: int, message: Optional[str] = None):
    if bool(os.getenv('AGENTSTACK_IS_TEST_ENV')):
        return

    try:
        requests.put(TELEMETRY_URL, json={"id": id, "result": result, "message": message})
    except Exception:
        pass

def _get_cli_user_guid() -> str:
    if Path(USER_GUID_FILE_PATH).exists():
        try:
            with open(USER_GUID_FILE_PATH, 'r') as f:
                return f.read()
        except (json.JSONDecodeError, PermissionError):
            return "unknown"

    # make new cli user guid
    try:
        # Create directory if it doesn't exist
        USER_GUID_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

        guid = str(uuid.uuid4())
        with open(USER_GUID_FILE_PATH, 'w') as f:
            f.write(guid)
        return guid
    except (OSError, PermissionError):
        # Silently fail in CI or when we can't write
        return "unknown"