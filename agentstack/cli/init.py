import os, sys
from typing import Optional
from pathlib import Path
from agentstack import conf, log
from agentstack.exceptions import EnvironmentError
from agentstack import packaging
from agentstack.cli import welcome_message, init_project_builder
from agentstack.utils import term_color


# TODO move the rest of the CLI init tooling into this file


def require_uv():
    try:
        uv_bin = packaging.get_uv_bin()
        assert os.path.exists(uv_bin)
    except (AssertionError, ImportError):
        message = "Error: uv is not installed."
        message += "Full installation instructions at: https://docs.astral.sh/uv/getting-started/installation"
        match sys.platform:
            case 'linux' | 'darwin':
                message += "Hint: run `curl -LsSf https://astral.sh/uv/install.sh | sh`"
            case _:
                pass
        raise EnvironmentError(message)


def init_project(
    slug_name: Optional[str] = None,
    template: Optional[str] = None,
    use_wizard: bool = False,
):
    """
    Initialize a new project in the current directory.

    - create a new virtual environment
    - copy project skeleton
    - install dependencies
    """
    require_uv()

    # TODO prevent the user from passing the --path arguent to init
    if slug_name:
        conf.set_path(conf.PATH / slug_name)
    else:
        raise Exception("Error: No project directory specified.\n Run `agentstack init <project_name>`")

    if os.path.exists(conf.PATH):  # cookiecutter requires the directory to not exist
        raise Exception(f"Error: Directory already exists: {conf.PATH}")

    welcome_message()
    log.notify("🦾 Creating a new AgentStack project...")
    log.info(f"Using project directory: {conf.PATH.absolute()}")

    # copy the project skeleton, create a virtual environment, and install dependencies
    init_project_builder(slug_name, template, use_wizard)
    packaging.create_venv()
    packaging.install_project()

    log.success("🚀 AgentStack project generated successfully!\n")
    log.info(
        "  To get started, activate the virtual environment with:\n"
        f"    cd {conf.PATH}\n"
        "    source .venv/bin/activate\n\n"
        "  Run your new agent with:\n"
        "    agentstack run\n\n"
        "  Or, run `agentstack quickstart` or `agentstack docs` for more next steps.\n"
    )
