from typing import Optional
from pathlib import Path
import ast
from agentstack.generation import astools
from . import SUPPORTED_FRAMEWORKS, ValidationError


ENTRYPOINT: Path = Path('src/crew.py')

class CrewFile:
    """
    Parses and manipulates the CrewAI entrypoint file.
    """
    tree: ast.AST
    _base_class: ast.ClassDef

    def __init__(self, path: Optional[Path] = None):
        if path is None: path = Path()
        try:
            with open(path/ENTRYPOINT, 'r') as f:
                self.tree = ast.parse(f.read())
        except (FileNotFoundError, SyntaxError) as e:
            raise ValidationError(f"Failed to parse {ENTRYPOINT}\n{e}")

    def get_base_class(self) -> ast.ClassDef:
        """A base class is a class decorated with `@CrewBase`."""
        if self._base_class is None: # Gets cached to save repeat iteration
            try:
                self._base_class = astools.find_class_with_decorator(self.tree, 'CrewBase')[0]
            except IndexError:
                raise ValidationError(f"`@CrewBase` decorated class not found in {self.ENTRYPOINT}")
        return self._base_class

    def get_crew_method(self) -> ast.FunctionDef:
        """A `crew` method is a method decorated with `@crew`."""
        try:
            base_class = self.get_base_class()
            return astools.find_decorated_method_in_class(base_class, 'crew')[0]
        except IndexError:
            raise ValidationError(f"`@crew` decorated method not found in `{base_class.name}` class in {self.ENTRYPOINT}")

    def get_task_methods(self) -> list[ast.FunctionDef]:
        """A `task` method is a method decorated with `@task`."""
        return astools.find_decorated_method_in_class(self.get_base_class(), 'task')

    def get_agent_methods(self) -> list[ast.FunctionDef]:
        """An `agent` method is a method decorated with `@agent`."""
        return astools.find_decorated_method_in_class(self.get_base_class(), 'agent')

def validate_project(path: Optional[Path] = None) -> None:
    """
    Validate that a CrewAI project is ready to run.
    Raises a frameworks.VaidationError if the project is not valid.
    """
    crew_file = CrewFile(path) # raises ValidationError
    # A valid project must have a class in the crew.py file decorated with `@CrewBase`
    class_node = crew_file.get_base_class() # raises ValidationError
    # The Crew class must have one method decorated with `@crew`
    crew_file.get_crew_method() # raises ValidationError

    # The Crew class must have one or more methods decorated with `@agent`
    if len(crew_file.get_task_methods()) < 1:
        raise ValidationError(
            f"`@task` decorated method not found in `{class_node.name}` class in {ENTRYPOINT}.\n"
            "Create a new task using `agentstack generate task <task_name>`.")

    # The Crew class must have one or more methods decorated with `@agent`
    if len(crew_file.get_agent_methods()) < 1:
        raise ValidationError(
            f"`@agent` decorated method not found in `{class_node.name}` class in {ENTRYPOINT}.\n"
            "Create a new agent using `agentstack generate agent <agent_name>`.")

def add_tool(path: Optional[Path] = None) -> None:
    """
    Add a tool to the CrewAI framework.

    Creates the tool's method in the Crew class in the entrypoint file and 
    imports the tool's methods from the tool module.
    """
    pass

def remove_tool(path: Optional[Path] = None) -> None:
    pass

def add_agent(path: Optional[Path] = None) -> None:
    pass

def remove_agent(path: Optional[Path] = None) -> None:
    pass

def add_input(path: Optional[Path] = None) -> None:
    pass

def remove_input(path: Optional[Path] = None) -> None:
    pass

