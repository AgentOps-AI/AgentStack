from typing import Optional
import sys
import traceback
from pathlib import Path
import importlib.util
from dotenv import load_dotenv

from agentstack import conf
from agentstack.exceptions import ValidationError
from agentstack import inputs
from agentstack import frameworks
from agentstack.utils import term_color, get_framework

MAIN_FILENAME: Path = Path("src/main.py")
MAIN_MODULE_NAME = "main"


def _format_friendy_error_message(exception: Exception):
    """
    Projects will throw various errors, especially on first runs, so we catch
    them here and print a more helpful message.

    In order to prevent us from having to import all possible backend exceptions
    we do string matching on the exception type and traceback contents.
    """
    # TODO These end up being pretty framework-specific; consider individual implementations.
    COMMON_LLM_ENV_VARS = (
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
    )

    name = exception.__class__.__name__
    message = str(exception)
    tracebacks = traceback.format_exception(type(exception), exception, exception.__traceback__)

    match (name, message, tracebacks):
        # The user doesn't have an environment variable set for the LLM provider.
        case ('AuthenticationError', m, t) if 'litellm.AuthenticationError' in t[-1]:
            variable_name = [k for k in COMMON_LLM_ENV_VARS if k in message] or ["correct"]
            return (
                "We were unable to connect to the LLM provider. "
                f"Ensure your .env file has the {variable_name[0]} variable set."
            )
        # This happens when the LLM configured for an agent is invalid.
        case ('BadRequestError', m, t) if 'LLM Provider NOT provided' in t[-1]:
            return (
                "An invalid LLM was configured for an agent. "
                "Ensure the 'llm' attribute of the agent in the agents.yaml file is in the format <provider>/<model>."
            )
        # The user has not configured the correct agent name in the tasks.yaml file.
        case ('KeyError', m, t) if 'self.tasks_config[task_name]["agent"]' in t[-2]:
            return (
                f"The agent {message} is not defined in your agents file. "
                "Ensure the 'agent' fields in your tasks.yaml correspond to an entry in the agents.yaml file."
            )
        # The user does not have an agent defined in agents.yaml file, but it does
        # exist in the entrypoint code.
        case ('KeyError', m, t) if 'config=self.agents_config[' in t[-2]:
            return (
                f"The agent {message} is not defined in your agents file. "
                "Ensure all agents referenced in your code are defined in the agents.yaml file."
            )
        # The user does not have a task defined in tasks.yaml file, but it does
        # exist in the entrypoint code.
        case ('KeyError', m, t) if 'config=self.tasks_config[' in t[-2]:
            return (
                f"The task {message} is not defined in your tasks. "
                "Ensure all tasks referenced in your code are defined in the tasks.yaml file."
            )
        case (_, _, _):
            return f"{name}: {message}, {tracebacks[-1]}"


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


def run_project(command: str = 'run', debug: bool = False, cli_args: Optional[str] = None):
    """Validate that the project is ready to run and then run it."""
    if conf.get_framework() not in frameworks.SUPPORTED_FRAMEWORKS:
        print(term_color(f"Framework {conf.get_framework()} is not supported by agentstack.", 'red'))
        sys.exit(1)

    try:
        frameworks.validate_project()
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

    load_dotenv(Path.home() / '.env')  # load the user's .env file
    load_dotenv(conf.PATH / '.env', override=True)  # load the project's .env file

    # import src/main.py from the project path and run `command` from the project's main.py
    try:
        print("Running your agent...")
        project_main = _import_project_module(conf.PATH)
        getattr(project_main, command)()
    except ImportError as e:
        print(term_color(f"Failed to import project. Does '{MAIN_FILENAME}' exist?:\n{e}", 'red'))
        sys.exit(1)
    except Exception as exception:
        if debug:
            raise exception
        print(term_color("\nAn error occurred while running your project:\n", 'red'))
        print(_format_friendy_error_message(exception))
        print(term_color("\nRun `agentstack run --debug` for a full traceback.", 'blue'))
        sys.exit(1)
