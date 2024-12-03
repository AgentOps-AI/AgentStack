import json
import os, sys
import time
from datetime import datetime
from pathlib import Path
from packaging.version import parse as parse_version, Version
import inquirer
from agentstack.utils import term_color, get_version, get_framework
from agentstack import packaging
from appdirs import user_data_dir


def _is_ci_environment():
    """Detect if we're running in a CI environment"""
    ci_env_vars = [
        'CI',
        'GITHUB_ACTIONS',
        'GITLAB_CI',
        'TRAVIS',
        'CIRCLECI',
        'JENKINS_URL',
        'TEAMCITY_VERSION'
    ]
    return any(os.getenv(var) for var in ci_env_vars)


# Try to get appropriate directory for storing update file
try:
    base_dir = Path(user_data_dir("agentstack", "agency"))
    # Test if we can write to directory
    test_file = base_dir / '.test_write_permission'
    test_file.touch()
    test_file.unlink()
except (RuntimeError, OSError, PermissionError):
    # In CI or when directory is not writable, use temp directory
    base_dir = Path(os.getenv('TEMP', '/tmp'))

LAST_CHECK_FILE_PATH = base_dir / ".cli-last-update"
INSTALL_PATH = Path(sys.executable).parent.parent
ENDPOINT_URL = "https://pypi.org/simple"
CHECK_EVERY = 3600  # hour


def get_latest_version(package: str) -> Version:
    """Get version information from PyPi to save a full package manager invocation"""
    import requests  # defer import until we know we need it
    response = requests.get(f"{ENDPOINT_URL}/{package}/", headers={"Accept": "application/vnd.pypi.simple.v1+json"})
    if response.status_code != 200:
        raise Exception(f"Failed to fetch package data from pypi.")
    data = response.json()
    return parse_version(data['versions'][-1])


def load_update_data():
    """Load existing update data or return empty dict if file doesn't exist"""
    if Path(LAST_CHECK_FILE_PATH).exists():
        try:
            with open(LAST_CHECK_FILE_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, PermissionError):
            return {}
    return {}


def should_update() -> bool:
    """Has it been longer than CHECK_EVERY since the last update check?"""
    # Always check for updates in CI
    if _is_ci_environment():
        return True

    data = load_update_data()
    last_check = data.get(str(INSTALL_PATH))

    if not last_check:
        return True

    return time.time() - last_check > CHECK_EVERY


def record_update_check():
    """Save current timestamp for this installation"""
    # Don't record updates in CI
    if _is_ci_environment():
        return

    try:
        data = load_update_data()
        data[str(INSTALL_PATH)] = datetime.now().isoformat()

        # Create directory if it doesn't exist
        LAST_CHECK_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(LAST_CHECK_FILE_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except (OSError, PermissionError):
        # Silently fail in CI or when we can't write
        pass


def check_for_updates(update_requested: bool = False):
    """
    `update_requested` indicates the user has explicitly requested an update.
    """
    if not update_requested and not should_update():
        return

    print("Checking for updates...\n")

    # always check agentstack, check others if requested
    packages_to_check = ['agentstack']
    if update_requested:
        framework = get_framework()
        packages_to_check += [framework, 'agentops']

    any_updated = False
    for package in packages_to_check:
        try:
            latest_version: Version = get_latest_version(package)
        except Exception as e:
            print(term_color("Failed to retrieve package index.", 'red'))
            return

        installed_version: Version = parse_version(get_version(package))
        if latest_version > installed_version:
            print('')  # newline
            if inquirer.confirm(f"New version of {package} available: {latest_version}! Do you want to install?"):
                # TODO: i dont like this explicit check here. we may need to have a
                # TODO: framework config eventually that can list supporting packages
                # TODO: these have to be run at the same time with `poetry add`
                # TODO: otherwise the dependency resolution fails
                if package == 'crewai':
                    package = 'crewai crewai-tools'
                packaging.upgrade(package)
                print(term_color(f"{package} updated. Re-run your command to use the latest version.", 'green'))
                any_updated = True
            else:
                print(term_color("Skipping update. Run `agentstack update` to install the latest version.", 'blue'))
        else:
            print(f"{package} is up to date ({installed_version})")

    record_update_check()

    if any_updated:
        sys.exit(0)
