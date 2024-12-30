import os
import sys
import json
from ruamel.yaml import YAML
import re
from importlib.metadata import version
from pathlib import Path
import importlib.resources
from agentstack import conf
from inquirer import errors as inquirer_errors


def get_version(package: str = 'agentstack'):
    try:
        return version(package)
    except (KeyError, FileNotFoundError) as e:
        print(e)
        return "Unknown version"


def verify_agentstack_project():
    try:
        agentstack_config = conf.ConfigFile()
    except FileNotFoundError:
        print(
            "\033[31mAgentStack Error: This does not appear to be an AgentStack project."
            "\nPlease ensure you're at the root directory of your project and a file named agentstack.json exists. "
            "If you're starting a new project, run `agentstack init`\033[0m"
        )
        sys.exit(1)


def get_package_path() -> Path:
    """This is the Path where agentstack is installed."""
    if sys.version_info <= (3, 9):
        return Path(sys.modules['agentstack'].__path__[0])
    return importlib.resources.files('agentstack')  # type: ignore[return-value]


def get_framework() -> str:
    """Assert that we're inside a valid project and return the framework name."""
    verify_agentstack_project()
    framework = conf.get_framework()
    assert framework  # verify_agentstack_project should catch this
    return framework


def get_telemetry_opt_out() -> bool:
    """
    Gets the telemetry opt out setting.
    First checks the environment variable AGENTSTACK_TELEMETRY_OPT_OUT.
    If that is not set, it checks the agentstack.json file.
    Otherwise we can assume the user has not opted out.
    """
    try:
        return bool(os.environ['AGENTSTACK_TELEMETRY_OPT_OUT'])
    except KeyError:
        agentstack_config = conf.ConfigFile()
        return bool(agentstack_config.telemetry_opt_out)
    except FileNotFoundError:
        return False


def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_to_camel(s):
    return ''.join(word.title() for word in s.split('_'))


def open_json_file(path) -> dict:
    with open(path, 'r') as f:
        data = json.load(f)
    return data


def open_yaml_file(path) -> dict:
    yaml = YAML()
    yaml.preserve_quotes = True  # Preserve quotes in existing data

    with open(path, 'r') as f:
        data = yaml.load(f)
    return data


def clean_input(input_string):
    special_char_pattern = re.compile(r'[^a-zA-Z0-9\s_]')
    return re.sub(special_char_pattern, '', input_string).lower().replace(' ', '_').replace('-', '_')


def term_color(text: str, color: str) -> str:
    colors = {
        'red': '91',
        'green': '92',
        'yellow': '93',
        'blue': '94',
        'purple': '95',
        'cyan': '96',
        'white': '97',
    }
    color_code = colors.get(color)
    if color_code:
        return f"\033[{color_code}m{text}\033[00m"
    else:
        return text


def is_snake_case(string: str):
    return bool(re.match('^[a-z0-9_]+$', string))


def validator_not_empty(min_length=1):
    def validator(_, answer):
        if len(answer) < min_length:
            raise inquirer_errors.ValidationError(
                '', reason=f"This field must be at least {min_length} characters long."
            )
        return True

    return validator
