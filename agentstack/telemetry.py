# hi :)
#
# if you're reading this, you probably saw "telemetry.py" and
# got mad and went to go see how we're spying on you
#
# i really hate to put this functionality in and was very
# resistant to it. as a human, i value privacy as a fundamental
# human right. but i also value my time.
#
# i have been putting a lot of my time into building out
# agentstack. i have strong conviction for what this project
# can be. it's showing some great progress, but for me to justify
# spending days and nights building this, i need to know that
# people are actually using it and not just starring the repo
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

import platform
import socket
import psutil
import requests
from agentstack.utils import get_telemetry_opt_out, get_framework, get_version

TELEMETRY_URL = 'https://api.agentstack.sh/telemetry'

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
        'agentstack_version': get_version()
    }

    if command != "init":
        telemetry_data['framework'] = get_framework()
    else:
        telemetry_data['framework'] = "n/a"

    # Attempt to get general location based on public IP
    try:
        response = requests.get('https://ipinfo.io/json')
        if response.status_code == 200:
            location_data = response.json()
            telemetry_data.update({
                'ip': location_data.get('ip'),
                'city': location_data.get('city'),
                'region': location_data.get('region'),
                'country': location_data.get('country')
            })
    except requests.RequestException as e:
        telemetry_data['location_error'] = str(e)

    return telemetry_data


def track_cli_command(command: str):
    try:
        data = collect_machine_telemetry(command)
        requests.post(TELEMETRY_URL, json={"command": command, **data})
    except:
        pass
