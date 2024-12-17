"""
Project generation utilities for AgentStack.

This module handles the generation of new projects using cookiecutter templates
and framework-specific configurations.
"""

import os
from pathlib import Path
import shutil
from cookiecutter.main import cookiecutter
from agentstack.utils import get_package_path
from agentstack.exceptions import ValidationError


def generate_project(project_dir: Path, framework: str, project_name: str, project_slug: str) -> None:
    """
    Generate a new project using the appropriate template for the specified framework.

    Args:
        project_dir: Directory where the project should be created
        framework: Name of the framework to use (e.g., 'crewai', 'agent_protocol')
        project_name: Human-readable name of the project
        project_slug: URL-friendly slug for the project
    """
    # Get absolute path to template directory using package path
    package_path = get_package_path()
    template_dir = package_path / 'templates' / framework

    # Validate template directory and cookiecutter.json existence
    if not template_dir.exists():
        raise ValidationError(
            f"Template directory for framework '{framework}' not found at {template_dir}. "
            f"Package path: {package_path}"
        )

    cookiecutter_json = template_dir / 'cookiecutter.json'
    if not cookiecutter_json.exists():
        raise ValidationError(
            f"cookiecutter.json not found in template directory at {cookiecutter_json}. "
            f"Directory contents: {list(template_dir.iterdir())}"
        )

    # Create project directory if it doesn't exist
    os.makedirs(project_dir, exist_ok=True)

    # Generate project using cookiecutter with absolute path
    cookiecutter(
        str(template_dir.absolute()),
        output_dir=str(project_dir.parent.absolute()),
        no_input=True,
        extra_context={
            'project_metadata': {
                'project_name': project_name,
                'project_slug': project_slug,
            }
        },
    )

    # Move contents from nested directory to project_dir
    nested_dir = project_dir.parent / project_slug
    if nested_dir.exists() and nested_dir != project_dir:
        for item in nested_dir.iterdir():
            target_path = project_dir / item.name
            if target_path.exists():
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
            shutil.move(str(item), str(target_path))
        nested_dir.rmdir()
