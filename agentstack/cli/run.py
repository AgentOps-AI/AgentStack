from typing import Optional
import sys
from pathlib import Path
import importlib.util
from dotenv import load_dotenv

from agentstack import ValidationError
from agentstack import inputs
from agentstack import frameworks
from agentstack.utils import term_color, get_framework

MAIN_FILENAME: Path = Path("src/main.py")
MAIN_MODULE_NAME = "main"


def _import_project_module(path: Path):
    """
    Import `main` from the project path.

    We do it this way instead of spawning a subprocess so that we can share
    state with the user's project.
    """
    spec = importlib.util.spec_from_file_location(MAIN_MODULE_NAME, str(path / MAIN_FILENAME))

    assert spec is not None  # appease type checker
    assert spec.loader is not None  # appease type checker

    project_module = importlib.util.module_from_spec(spec)
    sys.path.append(str((path / MAIN_FILENAME).parent))
    spec.loader.exec_module(project_module)
    return project_module


def run_project(command: str = 'run', path: Optional[str] = None, cli_args: Optional[str] = None):
    """Validate that the project is ready to run and then run it."""
    _path = Path(path) if path else Path.cwd()
    framework = get_framework(_path)

    if framework not in frameworks.SUPPORTED_FRAMEWORKS:
        print(term_color(f"Framework {framework} is not supported by agentstack.", 'red'))
        sys.exit(1)

    try:
        frameworks.validate_project(framework, _path)
    except ValidationError as e:
        print(term_color(f"Project validation failed:\n{e}", 'red'))
        sys.exit(1)

    # Parse extra --input-* arguments for runtime overrides of the project's inputs
    if cli_args:
        for arg in cli_args:
            if not arg.startswith('--input-'):
                continue
            key, value = arg[len('--input-') :].split('=')
            inputs.add_input_for_run(key, value)

    # explicitly load the project's .env file
    load_dotenv(_path / '.env')

    # import src/main.py from the project path
    try:
        project_main = _import_project_module(_path)
    except ImportError as e:
        print(term_color(f"Failed to import project. Does '{MAIN_FILENAME}' exist?:\n{e}", 'red'))
        sys.exit(1)

    # run `command` from the project's main.py
    # TODO try/except this and print detailed information with a --debug flag
    return getattr(project_main, command)()
