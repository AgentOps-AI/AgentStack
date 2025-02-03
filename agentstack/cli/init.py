import os, sys
from typing import Optional
from pathlib import Path
import inquirer
from textwrap import shorten

from agentstack import conf, log
from agentstack.exceptions import EnvironmentError
from agentstack.utils import is_snake_case
from agentstack import packaging
from agentstack import frameworks
from agentstack import generation
from agentstack.proj_templates import get_all_templates, TemplateConfig

from agentstack.cli import welcome_message
from agentstack.cli.wizard import run_wizard
from agentstack.cli.templates import insert_template


def require_uv():
    try:
        uv_bin = packaging.get_uv_bin()
        assert os.path.exists(uv_bin)
    except (AssertionError, ImportError):
        message = (
            "Error: uv is not installed.\n"
            "Full installation instructions at: "
            "https://docs.astral.sh/uv/getting-started/installation\n"
        )
        match sys.platform:
            case 'linux' | 'darwin':
                message += "Hint: run `curl -LsSf https://astral.sh/uv/install.sh | sh`\n"
            case _:
                pass
        raise EnvironmentError(message)


def select_template(slug_name: str, framework: Optional[str] = None) -> TemplateConfig:
    """Let the user select a template from the ones available."""
    templates: list[TemplateConfig] = get_all_templates()

    EMPTY = 'empty'
    choices = [
        (EMPTY, "🆕 Empty Project"),
    ]
    for template in templates:
        choices.append((template.name, shorten(f"⚡️ {template.name} - {template.description}", 80)))

    choice = inquirer.list_input(
        message="Do you want to start with a template?",
        choices=[c[1] for c in choices],
    )
    template_name = next(c[0] for c in choices if c[1] == choice)

    if template_name == EMPTY:
        return TemplateConfig(
            name=slug_name,
            description="",
            framework=framework or frameworks.DEFAULT_FRAMEWORK,
        )

    return TemplateConfig.from_template_name(template_name)


def init_project(
    slug_name: Optional[str] = None,
    template: Optional[str] = None,
    framework: Optional[str] = None,
    use_wizard: bool = False,
):
    """
    Initialize a new project in the current directory.

    - create a new virtual environment
    - copy project skeleton
    - install dependencies
    - insert Tasks, Agents and Tools
    """
    require_uv()

    # TODO prevent the user from passing the --path argument to init
    if slug_name:
        if not is_snake_case(slug_name):
            raise Exception("Project name must be snake_case")
        conf.set_path(conf.PATH / slug_name)
    else:
        raise Exception("No project directory specified.\n Run `agentstack init <project_name>`")

    if os.path.exists(conf.PATH):  # cookiecutter requires the directory to not exist
        raise Exception(f"Directory already exists: {conf.PATH}")

    if template and use_wizard:
        raise Exception("Template and wizard flags cannot be used together")

    welcome_message()

    if use_wizard:
        log.debug("Initializing new project with wizard.")
        template_data = run_wizard(slug_name)
    elif template:
        log.debug(f"Initializing new project with template: {template}")
        template_data = TemplateConfig.from_user_input(template)
    else:
        log.debug("Initializing new project with template selection.")
        template_data = select_template(slug_name, framework)

    log.notify("🦾 Creating a new AgentStack project...")
    log.info(f"Using project directory: {conf.PATH.absolute()}")

    if framework is None:
        framework = template_data.framework
    if not framework in frameworks.SUPPORTED_FRAMEWORKS:
        raise Exception(f"Framework '{framework}' is not supported.")
    log.info(f"Using framework: {framework}")

    # copy the project skeleton, create a virtual environment, and install dependencies
    # project template is populated before the venv is created so we have a working directory
    insert_template(name=slug_name, template=template_data, framework=framework)
    log.info("Creating virtual environment...")
    packaging.create_venv()
    log.info("Installing dependencies...")
    packaging.install_project()

    # now we can interact with the project and add Agents, Tasks, and Tools
    # we allow dependencies to be installed along with these, so the project must
    # be fully initialized first.
    for task in template_data.tasks:
        generation.add_task(**task.model_dump())

    for agent in template_data.agents:
        generation.add_agent(**agent.model_dump())

    for tool in template_data.tools:
        generation.add_tool(**tool.model_dump())

    log.success("🚀 AgentStack project generated successfully!\n")
    log.info(
        "  To get started, activate the virtual environment with:\n"
        f"    💫 cd {conf.PATH}\n"
        "    🌟 source .venv/bin/activate\n\n"
        "  Run your new agent with:\n"
        "    ✨ agentstack run\n\n"
        "  Or, run `agentstack quickstart` or `agentstack docs` for more next steps.\n"
    )
