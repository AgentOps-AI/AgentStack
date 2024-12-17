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
    template_dir = get_package_path() / 'templates' / framework

    if not template_dir.exists():
        raise ValidationError(f"Template directory for framework '{framework}' not found")

    # Create project directory if it doesn't exist
    os.makedirs(project_dir, exist_ok=True)

    # Generate project using cookiecutter
    cookiecutter(
        str(template_dir),
        output_dir=str(project_dir.parent),
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
            shutil.move(str(item), str(project_dir / item.name))
        nested_dir.rmdir()
