import os, sys
from typing import Optional
from pathlib import Path
from agentstack import conf
from agentstack import packaging
from agentstack.cli import welcome_message, init_project_builder
from agentstack.utils import term_color


# TODO move the rest of the CLI init tooling into this file


def require_uv():
    try:
        uv_bin = packaging.get_uv_bin()
        assert os.path.exists(uv_bin)
    except (AssertionError, ImportError):
        print(term_color("Error: uv is not installed.", 'red'))
        print("Full installation instructions at: https://docs.astral.sh/uv/getting-started/installation")
        match sys.platform:
            case 'linux' | 'darwin':
                print("Hint: run `curl -LsSf https://astral.sh/uv/install.sh | sh`")
            case _:
                pass
        sys.exit(1)


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
    welcome_message()

    # conf.PATH may have been set by the argument parser, but if not, use the slug_name
    if slug_name:
        conf.set_path(conf.PATH / slug_name)
    else:
        print("Error: No project directory specified.")
        print("Run `agentstack init <project_name> or use the --path flag.")
        sys.exit(1)

    if os.path.exists(conf.PATH):
        print(f"Error: Directory already exists: {conf.PATH}")
        sys.exit(1)

    print(term_color("🦾 Creating a new AgentStack project...", 'blue'))
    print(f"Using project directory: {conf.PATH.absolute()}")
    # copy the project skeleton, create a virtual environment, and install dependencies
    init_project_builder(slug_name, template, use_wizard)
    packaging.create_venv()
    packaging.install('.')

    print(
        "\n"
        "🚀 \033[92mAgentStack project generated successfully!\033[0m\n\n"
        "  To get started, activate the virtual environment with:\n"
        f"    cd {conf.PATH}\n"
        "    source .venv/bin/activate\n\n"
        "  Run your new agent with:\n"
        "    agentstack run\n\n"
        "  Or, run `agentstack quickstart` or `agentstack docs` for more next steps.\n"
    )
