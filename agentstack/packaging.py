import os, sys
from typing import Optional, Callable
from pathlib import Path
import re
import subprocess
import select
from agentstack import conf
from agentstack.exceptions import EnvironmentError


DEFAULT_PYTHON_VERSION = "3.12"
VENV_DIR_NAME: Path = Path(".venv")


def install(package: str):
    """
    Install a package with `uv`.
    Filter output to only show useful progress messages.
    """
    RE_USEFUL_PROGRESS = re.compile(r'^(Resolved|Prepared|Installed|Audited)')

    def on_progress(line: str):
        # only print these four messages:
        # Resolved 78 packages in 225ms
        # Prepared 12 packages in 915ms
        # Installed 78 packages in 65ms
        # Audited 1 package in 28ms
        if RE_USEFUL_PROGRESS.match(line):
            print(line.strip())

    def on_error(line: str):
        print(f"uv: [error]\n {line.strip()}")

    # explicitly specify the --python executable to use so that the packages
    # are installed into the correct virtual environment
    _wrap_command_with_callbacks(
        [get_uv_bin(), 'pip', 'install', '--python', '.venv/bin/python', package],
        on_progress=on_progress,
        on_error=on_error,
    )


def remove(package: str):
    raise NotImplementedError("TODO `packaging.remove`")


def upgrade(package: str):
    raise NotImplementedError("TODO `packaging.upgrade`")


def create_venv(python_version: str = DEFAULT_PYTHON_VERSION):
    """Intialize a virtual environment in the project directory of one does not exist."""
    if os.path.exists(conf.PATH / VENV_DIR_NAME):
        return  # venv already exists

    RE_USEFUL_PROGRESS = re.compile(r'^(Using|Creating)')

    def on_progress(line: str):
        if RE_USEFUL_PROGRESS.match(line):
            print(line.strip())

    def on_error(line: str):
        print(f"uv: [error]\n {line.strip()}")

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
    env.setdefault("VIRTUAL_ENV", VENV_DIR_NAME)
    env["UV_INTERNAL__PARENT_INTERPRETER"] = sys.executable
    return env


def _wrap_command_with_callbacks(
    command: list[str],
    on_progress: Callable[[str], None] = lambda x: None,
    on_complete: Callable[[str], None] = lambda x: None,
    on_error: Callable[[str], None] = lambda x: None,
) -> None:
    """Run a command with progress callbacks."""
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
        else:
            on_error(all_lines)
    except Exception as e:
        on_error(str(e))
    finally:
        try:
            process.terminate()
        except:
            pass
