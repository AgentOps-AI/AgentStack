import os, sys
from typing import Optional, Callable
from pathlib import Path
import re
import subprocess
import select
from packaging.requirements import Requirement
from agentstack import conf, log


DEFAULT_PYTHON_VERSION = "3.12"
VENV_DIR_NAME: Path = Path(".venv")

# filter uv output by these words to only show useful progress messages
RE_UV_PROGRESS = re.compile(r'^(Resolved|Prepared|Installed|Uninstalled|Audited)')


# When calling `uv` we explicitly specify the --python executable to use so that
# the packages are installed into the correct virtual environment.
# In testing, when this was not set, packages could end up in the pyenv's
# site-packages directory; it's possible an environment variable can control this.


def install(package: str):
    """Install a package with `uv` and add it to pyproject.toml."""

    def on_progress(line: str):
        if RE_UV_PROGRESS.match(line):
            log.info(line.strip())

    def on_error(line: str):
        log.error(f"uv: [error]\n {line.strip()}")

    log.info(f"Installing {package}")
    _wrap_command_with_callbacks(
        [get_uv_bin(), 'add', '--python', '.venv/bin/python', package],
        on_progress=on_progress,
        on_error=on_error,
    )


def install_project():
    """Install all dependencies for the user's project."""

    def on_progress(line: str):
        if RE_UV_PROGRESS.match(line):
            log.info(line.strip())

    def on_error(line: str):
        log.error(f"uv: [error]\n {line.strip()}")

    try:
        result = _wrap_command_with_callbacks(
            [get_uv_bin(), 'pip', 'install', '--python', '.venv/bin/python', '.'],
            on_progress=on_progress,
            on_error=on_error,
        )
        if result is False:
            log.info("Retrying uv installation with --no-cache flag...")
            _wrap_command_with_callbacks(
                [get_uv_bin(), 'pip', 'install', '--no-cache', '--python', '.venv/bin/python', '.'],
                on_progress=on_progress,
                on_error=on_error,
            )
    except Exception as e:
        log.error(f"Installation failed: {str(e)}")
        raise


def remove(package: str):
    """Uninstall a package with `uv`."""
    # If `package` has been provided with a version, it will be stripped.
    requirement = Requirement(package)

    # TODO it may be worth considering removing unused sub-dependencies as well
    def on_progress(line: str):
        if RE_UV_PROGRESS.match(line):
            log.info(line.strip())

    def on_error(line: str):
        log.error(f"uv: [error]\n {line.strip()}")

    log.info(f"Uninstalling {requirement.name}")
    _wrap_command_with_callbacks(
        [get_uv_bin(), 'remove', '--python', '.venv/bin/python', requirement.name],
        on_progress=on_progress,
        on_error=on_error,
    )


def upgrade(package: str):
    """Upgrade a package with `uv`."""

    # TODO should we try to update the project's pyproject.toml as well?
    def on_progress(line: str):
        if RE_UV_PROGRESS.match(line):
            log.info(line.strip())

    def on_error(line: str):
        log.error(f"uv: [error]\n {line.strip()}")

    log.info(f"Upgrading {package}")
    _wrap_command_with_callbacks(
        [get_uv_bin(), 'pip', 'install', '-U', '--python', '.venv/bin/python', package],
        on_progress=on_progress,
        on_error=on_error,
    )


def create_venv(python_version: str = DEFAULT_PYTHON_VERSION):
    """Initialize a virtual environment in the project directory of one does not exist."""
    if os.path.exists(conf.PATH / VENV_DIR_NAME):
        return  # venv already exists

    RE_VENV_PROGRESS = re.compile(r'^(Using|Creating)')

    def on_progress(line: str):
        if RE_VENV_PROGRESS.match(line):
            log.info(line.strip())

    def on_error(line: str):
        log.error(f"uv: [error]\n {line.strip()}")

    _wrap_command_with_callbacks(
        [get_uv_bin(), 'venv', '--python', python_version],
        on_progress=on_progress,
        on_error=on_error,
    )


def get_uv_bin() -> str:
    """Find the path to the uv binary."""
    try:
        import uv

        return uv.find_uv_bin()
    except ImportError as e:
        raise e


def _setup_env() -> dict[str, str]:
    """Copy the current environment and add the virtual environment path for use by a subprocess."""
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = str(conf.PATH / VENV_DIR_NAME.absolute())
    env["UV_INTERNAL__PARENT_INTERPRETER"] = sys.executable
    return env


def _wrap_command_with_callbacks(
    command: list[str],
    on_progress: Callable[[str], None] = lambda x: None,
    on_complete: Callable[[str], None] = lambda x: None,
    on_error: Callable[[str], None] = lambda x: None,
) -> bool:
    """Run a command with progress callbacks. Returns bool for cmd success."""
    process = None
    try:
        all_lines = ''
        process = subprocess.Popen(
            command,
            cwd=conf.PATH.absolute(),
            env=_setup_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert process.stdout and process.stderr  # appease type checker

        readable = [process.stdout, process.stderr]
        while readable:
            ready, _, _ = select.select(readable, [], [])
            for fd in ready:
                line = fd.readline()
                if not line:
                    readable.remove(fd)
                    continue

                on_progress(line)
                all_lines += line

        if process.wait() == 0:  # return code: success
            on_complete(all_lines)
            return True
        else:
            on_error(all_lines)
            return False
    except Exception as e:
        on_error(str(e))
        return False
    finally:
        if process:
            try:
                process.terminate()
            except:
                pass
