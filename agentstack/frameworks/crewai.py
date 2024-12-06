from typing import Optional
from pathlib import Path
import ast
from agentstack import ValidationError
from agentstack.tools import ToolConfig
from agentstack.tasks import TaskConfig
from agentstack.agents import AgentConfig
from agentstack.generation import asttools


ENTRYPOINT: Path = Path('src/crew.py')

class CrewFile(asttools.File):
    """
    Parses and manipulates the CrewAI entrypoint file.
    All AST interactions should happen within the methods of this class.
    """
    _base_class: ast.ClassDef = None

    def get_base_class(self) -> ast.ClassDef:
        """A base class is a class decorated with `@CrewBase`."""
        if self._base_class is None: # Gets cached to save repeat iteration
            try:
                self._base_class = asttools.find_class_with_decorator(self.tree, 'CrewBase')[0]
            except IndexError:
                raise ValidationError(f"`@CrewBase` decorated class not found in {ENTRYPOINT}")
        return self._base_class

    def get_crew_method(self) -> ast.FunctionDef:
        """A `crew` method is a method decorated with `@crew`."""
        try:
            base_class = self.get_base_class()
            return asttools.find_decorated_method_in_class(base_class, 'crew')[0]
        except IndexError:
            raise ValidationError(f"`@crew` decorated method not found in `{base_class.name}` class in {ENTRYPOINT}")

    def get_task_methods(self) -> list[ast.FunctionDef]:
        """A `task` method is a method decorated with `@task`."""
        return asttools.find_decorated_method_in_class(self.get_base_class(), 'task')

    def add_task_method(self, task: TaskConfig):
        """Add a new task method to the CrewAI entrypoint."""
        task_methods = self.get_task_methods()
        if task.name in [method.name for method in task_methods]:
            # TODO this should check all methods in the class for duplicates
            raise ValidationError(f"Task `{task.name}` already exists in {ENTRYPOINT}")
        if task_methods:
            # Add after the existing task methods
            _, pos = self.get_node_range(task_methods[-1])
        else:
            # Add before the `crew` method
            crew_method = self.get_crew_method()
            pos, _ = self.get_node_range(crew_method)
        
        code = f"""    @task
    def {task.name}(self) -> Task:
        return Task(
            config=self.tasks_config['{task.name}'],
        )"""
        if not self.source[:pos].endswith('\n'):
            code = '\n\n' + code
        if not self.source[pos:].startswith('\n'):
            code += '\n\n'
        self.edit_node_range(pos, pos, code)

    def get_agent_methods(self) -> list[ast.FunctionDef]:
        """An `agent` method is a method decorated with `@agent`."""
        return asttools.find_decorated_method_in_class(self.get_base_class(), 'agent')

    def add_agent_method(self, agent: AgentConfig):
        """Add a new agent method to the CrewAI entrypoint."""
        # TODO do we want to pre-populate any tools?
        agent_methods = self.get_agent_methods()
        if agent.name in [method.name for method in agent_methods]:
            # TODO this should check all methods in the class for duplicates
            raise ValidationError(f"Agent `{agent.name}` already exists in {ENTRYPOINT}")
        if agent_methods:
            # Add after the existing agent methods
            _, pos = self.get_node_range(agent_methods[-1])
        else:
            # Add before the `crew` method
            crew_method = self.get_crew_method()
            pos, _ = self.get_node_range(crew_method)
        
        code = f"""    @agent
    def {agent.name}(self) -> Agent:
        return Agent(
            config=self.agents_config['{agent.name}'],
            tools=[], # add tools here or use `agentstack tools add <tool_name>
            verbose=True,
        )"""
        if not self.source[:pos].endswith('\n'):
            code = '\n\n' + code
        if not self.source[pos:].startswith('\n'):
            code += '\n\n'
        self.edit_node_range(pos, pos, code)

    def get_agent_tools(self, agent_name: str) -> ast.List:
        """
        Get the tools used by an agent as AST nodes.
        
        Tool definitons are inside of the methods marked with an `@agent` decorator.
        The method returns a new class instance with the tools as a list of callables
        under the kwarg `tools`.
        """
        method = asttools.find_method(self.get_agent_methods(), agent_name)
        if method is None:
            raise ValidationError(f"`@agent` method `{agent_name}` does not exist in {ENTRYPOINT}")
        
        agent_class = asttools.find_class_instantiation(method, 'Agent')
        if agent_class is None:
            raise ValidationError(f"`@agent` method `{agent_name}` does not have an `Agent` class instantiation in {ENTRYPOINT}")
        
        tools_kwarg = asttools.find_kwarg_in_method_call(agent_class, 'tools')
        if not tools_kwarg:
            raise ValidationError(f"`@agent` method `{agent_name}` does not have a keyword argument `tools` in {ENTRYPOINT}")

        return tools_kwarg.value

    def add_agent_tools(self, agent_name: str, tool: ToolConfig):
        """
        Add new tools to be used by an agent.
        
        Tool definitons are inside of the methods marked with an `@agent` decorator.
        The method returns a new class instance with the tools as a list of callables
        under the kwarg `tools`.
        """
        method = asttools.find_method(self.get_agent_methods(), agent_name)
        if method is None:
            raise ValidationError(f"`@agent` method `{agent_name}` does not exist in {ENTRYPOINT}")
        
        new_tool_nodes = []
        for tool_name in tool.tools:
            # This prefixes the tool name with the 'tools' module
            node = asttools.create_attribute('tools', tool_name)
            if tool.tools_bundled: # Splat the variable if it's bundled
                node = ast.Starred(value=node, ctx=ast.Load())
            new_tool_nodes.append(node)
        
        existing_node: ast.List = self.get_agent_tools(agent_name)
        new_node = ast.List(
            elts=set(existing_node.elts + new_tool_nodes),
            ctx=ast.Load()
        )
        start, end = self.get_node_range(existing_node)
        self.edit_node_range(start, end, new_node)
    
    def remove_agent_tools(self, agent_name: str, tool: ToolConfig):
        """
        Remove tools from an agent belonging to `tool`.
        """
        existing_node: ast.List = self.get_agent_tools(agent_name)
        start, end = self.get_node_range(existing_node)
        
        # modify the existing node to remove any matching tools
        for tool_name in tool.tools:
            for node in existing_node.elts:
                if isinstance(node, ast.Starred):
                    attr_name = node.value.attr
                else:
                    attr_name = node.attr
                if attr_name == tool_name:
                    existing_node.elts.remove(node)
        
        self.edit_node_range(start, end, existing_node)


def validate_project(path: Optional[Path] = None) -> None:
    """
    Validate that a CrewAI project is ready to run.
    Raises an `agentstack.VaidationError` if the project is not valid.
    """
    if path is None: path = Path()
    try:
        crew_file = CrewFile(path/ENTRYPOINT)
    except ValidationError as e:
        raise e

    # A valid project must have a class in the crew.py file decorated with `@CrewBase`
    try:
        class_node = crew_file.get_base_class()
    except ValidationError as e:
        raise e

    # The Crew class must have one method decorated with `@crew`
    try:
        crew_file.get_crew_method()
    except ValidationError as e:
        raise e

    # The Crew class must have one or more methods decorated with `@task`
    if len(crew_file.get_task_methods()) < 1:
        raise ValidationError(
            f"`@task` decorated method not found in `{class_node.name}` class in {ENTRYPOINT}.\n"
            "Create a new task using `agentstack generate task <task_name>`.")

    # The Crew class must have one or more methods decorated with `@agent`
    if len(crew_file.get_agent_methods()) < 1:
        raise ValidationError(
            f"`@agent` decorated method not found in `{class_node.name}` class in {ENTRYPOINT}.\n"
            "Create a new agent using `agentstack generate agent <agent_name>`.")

def get_task_names(path: Optional[Path] = None) -> list[str]:
    """
    Get a list of task names (methods with an @task decorator).
    """
    if path is None: path = Path()
    crew_file = CrewFile(path/ENTRYPOINT)
    return [method.name for method in crew_file.get_task_methods()]

def add_task(task: TaskConfig, path: Optional[Path] = None) -> None:
    """
    Add a task method to the CrewAI entrypoint.
    """
    if path is None: path = Path()
    with CrewFile(path/ENTRYPOINT) as crew_file:
        crew_file.add_task_method(task)

def get_agent_names(path: Optional[Path] = None) -> list[str]:
    """
    Get a list of agent names (methods with an @agent decorator).
    """
    if path is None: path = Path()
    crew_file = CrewFile(path/ENTRYPOINT)
    return [method.name for method in crew_file.get_agent_methods()]

def add_agent(agent: AgentConfig, path: Optional[Path] = None) -> None:
    """
    Add an agent method to the CrewAI entrypoint.
    """
    if path is None: path = Path()
    with CrewFile(path/ENTRYPOINT) as crew_file:
        crew_file.add_agent_method(agent)

def add_tool(tool: ToolConfig, agent_name: str, path: Optional[Path] = None):
    """
    Add a tool to the CrewAI entrypoint for the specified agent.
    The agent should already exist in the crew class and have a keyword argument `tools`.
    """
    if path is None: path = Path()
    with CrewFile(path/ENTRYPOINT) as crew_file:
        crew_file.add_agent_tools(agent_name, tool)

def remove_tool(tool: ToolConfig, agent_name: str, path: Optional[Path] = None):
    """
    Remove a tool from the CrewAI framework for the specified agent.
    """
    if path is None: path = Path()
    with CrewFile(path/ENTRYPOINT) as crew_file:
        crew_file.remove_agent_tools(agent_name, tool)

