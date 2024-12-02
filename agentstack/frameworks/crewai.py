from typing import Optional
from pathlib import Path
import ast
from . import SUPPORTED_FRAMEWORKS, ValidationError


ENTRYPOINT: Path = Path('src/crew.py')

def validate_project(path: Optional[Path] = None) -> None:
    """
    Validate that a CrewAI project is ready to run.
    Raises a frameworks.VaidationError if the project is not valid.
    """
    try:
        if path is None: path = Path()
        with open(path/ENTRYPOINT, 'r') as f:
            tree = ast.parse(f.read())
    except (FileNotFoundError, SyntaxError) as e:
        raise ValidationError(f"Failed to parse {ENTRYPOINT}\n {e}")

    # A valid project must have a class in the crew.py file decorated with `@CrewBase`
    try:
        class_node = _find_class_with_decorator(tree, 'CrewBase')[0]
    except IndexError:
        raise ValidationError(f"`@CrewBase` decorated class not found in {ENTRYPOINT}")

    # The Crew class must have one or more methods decorated with `@agent`
    if len(_find_decorated_method_in_class(class_node, 'task')) < 1:
        raise ValidationError(f"`@task` decorated method not found in `{class_node.name}` class in {ENTRYPOINT}")

    # The Crew class must have one or more methods decorated with `@agent`
    if len(_find_decorated_method_in_class(class_node, 'agent')) < 1:
        raise ValidationError(f"`@agent` decorated method not found in `{class_node.name}` class in {ENTRYPOINT}")

    # The Crew class must have one method decorated with `@crew`
    if len(_find_decorated_method_in_class(class_node, 'crew')) < 1:
        raise ValidationError(f"`@crew` decorated method not found in `{class_node.name}` class in {ENTRYPOINT}")

# TODO move these to a shared AST utility module
def _find_class_with_decorator(tree: ast.AST, decorator_name: str) -> list[ast.ClassDef]:
    """Find a class definition that is marked by a decorator in an AST."""
    nodes = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id == decorator_name:
                    nodes.append(node)
    return nodes

def _find_decorated_method_in_class(classdef: ast.ClassDef, decorator_name: str) -> list[ast.FunctionDef]:
    """Find all method definitions in a class definition which are decorated with a specific decorator."""
    nodes = []
    for node in ast.iter_child_nodes(classdef):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id == decorator_name:
                    nodes.append(node)
    return nodes

