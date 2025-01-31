from typing import TYPE_CHECKING, Optional, Any, Callable
from pathlib import Path
import ast
from agentstack import conf, log
from agentstack.exceptions import ValidationError
from agentstack._tools import ToolConfig
from agentstack.tasks import TaskConfig
from agentstack.agents import AgentConfig
from agentstack.generation import asttools
from agentstack import graph

if TYPE_CHECKING:
    from agentstack.generation import InsertionPoint

ENTRYPOINT: Path = Path('src/crew.py')


class CrewFile(asttools.File):
    """
    Parses and manipulates the CrewAI entrypoint file.
    All AST interactions should happen within the methods of this class.
    """

    def write(self):
        """
        Early versions of the crew entrypoint file used tabs instead of spaces.
        This method replaces all tabs with 4 spaces before writing the file to
        avoid SyntaxErrors.
        """
        self.source = self.source.replace('\t', '    ')
        super().write()

    def get_base_class(self) -> ast.ClassDef:
        """A base class is a class decorated with `@CrewBase`."""
        try:
            return asttools.find_class_with_decorator(self.tree, 'CrewBase')[0]
        except IndexError:
            raise ValidationError(f"`@CrewBase` decorated class not found in {ENTRYPOINT}")

    def get_crew_method(self) -> ast.FunctionDef:
        """A `crew` method is a method decorated with `@crew`."""
        try:
            base_class = self.get_base_class()
            return asttools.find_decorated_method_in_class(base_class, 'crew')[0]
        except IndexError:
            raise ValidationError(
                f"`@crew` decorated method not found in `{base_class.name}` class in {ENTRYPOINT}"
            )

    def get_task_methods(self) -> list[ast.FunctionDef]:
        """A `task` method is a method decorated with `@task`."""
        return asttools.find_decorated_method_in_class(self.get_base_class(), 'task')

    def add_task_method(self, task: TaskConfig):
        """Add a new task method to the CrewAI entrypoint."""
        task_methods = self.get_task_methods()
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

        Tool definitions are inside of the methods marked with an `@agent` decorator.
        The method returns a new class instance with the tools as a list of callables
        under the kwarg `tools`.
        """
        method = asttools.find_method(self.get_agent_methods(), agent_name)
        if method is None:
            raise ValidationError(f"`@agent` method `{agent_name}` does not exist in {ENTRYPOINT}")

        agent_class = asttools.find_class_instantiation(method, 'Agent')
        if agent_class is None:
            raise ValidationError(
                f"`@agent` method `{agent_name}` does not have an `Agent` class instantiation in {ENTRYPOINT}"
            )

        tools_kwarg = asttools.find_kwarg_in_method_call(agent_class, 'tools')
        if not tools_kwarg:
            raise ValidationError(
                f"`@agent` method `{agent_name}` does not have a keyword argument `tools` in {ENTRYPOINT}"
            )

        if not isinstance(tools_kwarg.value, ast.List):
            raise ValidationError(
                f"`@agent` method `{agent_name}` has a non-list value for the `tools` kwarg in {ENTRYPOINT}"
            )

        return tools_kwarg.value

    def get_agent_tool_nodes(self, agent_name: str) -> list[ast.Starred]:
        """
        Get a list of all ast nodes that define agentstack tools used by the agent.
        """
        agent_tools_node = self.get_agent_tools(agent_name)
        return asttools.find_tool_nodes(agent_tools_node)

    def get_agent_tool_names(self, agent_name: str) -> list[str]:
        """
        Get a list of all tools used by the agent.

        Tools are identified by the item name of an `agentstack.tools` attribute node.
        """
        tool_names: list[str] = []
        for node in self.get_agent_tool_nodes(agent_name):
            # ignore type checking here since `get_agent_tool_nodes` is exhaustive
            tool_names.append(node.value.slice.value)  # type: ignore[attr-defined]
        return tool_names

    def add_agent_tools(self, agent_name: str, tool: ToolConfig):
        """
        Add new tools to be used by an agent.

        Tool definitions are inside the methods marked with an `@agent` decorator.
        The method returns a new class instance with the tools as a list of callables
        under the kwarg `tools`.
        """
        method = asttools.find_method(self.get_agent_methods(), agent_name)
        if method is None:
            raise ValidationError(f"`@agent` method `{agent_name}` does not exist in {ENTRYPOINT}")

        existing_node: ast.List = self.get_agent_tools(agent_name)
        existing_elts: list[ast.expr] = existing_node.elts

        new_tool_nodes: list[ast.expr] = []
        if not tool.name in self.get_agent_tool_names(agent_name):
            existing_elts.append(asttools.create_tool_node(tool.name))

        new_node = ast.List(elts=existing_elts, ctx=ast.Load())
        start, end = self.get_node_range(existing_node)
        self.edit_node_range(start, end, new_node)

    def remove_agent_tools(self, agent_name: str, tool: ToolConfig):
        """
        Remove tools from an agent belonging to `tool`.
        """
        existing_node: ast.List = self.get_agent_tools(agent_name)
        start, end = self.get_node_range(existing_node)

        # modify the existing node to remove any matching tools
        # we're referencing the internal node list from two directions here,
        # so it's important that the node tree doesn't get re-parsed in between
        for node in self.get_agent_tool_nodes(agent_name):
            # ignore type checking here since `get_agent_tool_nodes` is exhaustive
            if tool.name == node.value.slice.value:  # type: ignore[attr-defined]
                existing_node.elts.remove(node)

        self.edit_node_range(start, end, existing_node)


def validate_project() -> None:
    """
    Validate that a CrewAI project is ready to run.
    Raises an `agentstack.ValidationError` if the project is not valid.
    """
    try:
        crew_file = CrewFile(conf.PATH / ENTRYPOINT)
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
            "Create a new task using `agentstack generate task <task_name>`."
        )

    # The Crew class must have one or more methods decorated with `@agent`
    if len(crew_file.get_agent_methods()) < 1:
        raise ValidationError(
            f"`@agent` decorated method not found in `{class_node.name}` class in {ENTRYPOINT}.\n"
            "Create a new agent using `agentstack generate agent <agent_name>`."
        )


def parse_llm(llm: str) -> tuple[str, str]:
    """
    Parse the llm string into a `LLM` dataclass.
    Crew separates providers and models with a forward slash.
    """
    provider, model = llm.split('/')
    return provider, model


def get_task_method_names() -> list[str]:
    """
    Get a list of task names (methods with an @task decorator).
    """
    crew_file = CrewFile(conf.PATH / ENTRYPOINT)
    return [method.name for method in crew_file.get_task_methods()]


def add_task(task: TaskConfig, position: Optional['InsertionPoint'] = None) -> None:
    """
    Add a task method to the CrewAI entrypoint.
    """
    if position is not None:
        raise NotImplementedError("Task insertion points are not supported in CrewAI.")

    with CrewFile(conf.PATH / ENTRYPOINT) as crew_file:
        crew_file.add_task_method(task)


def get_agent_method_names() -> list[str]:
    """
    Get a list of agent names (methods with an @agent decorator).
    """
    crew_file = CrewFile(conf.PATH / ENTRYPOINT)
    return [method.name for method in crew_file.get_agent_methods()]


def get_agent_tool_names(agent_name: str) -> list[Any]:
    """
    Get a list of tools used by an agent.
    """
    with CrewFile(conf.PATH / ENTRYPOINT) as crew_file:
        return crew_file.get_agent_tool_names(agent_name)


def add_agent(agent: AgentConfig, position: Optional['InsertionPoint'] = None) -> None:
    """
    Add an agent method to the CrewAI entrypoint.
    """
    if position is not None:
        raise NotImplementedError("Agent insertion points are not supported in CrewAI.")

    with CrewFile(conf.PATH / ENTRYPOINT) as crew_file:
        crew_file.add_agent_method(agent)


def add_tool(tool: ToolConfig, agent_name: str):
    """
    Add a tool to the CrewAI entrypoint for the specified agent.
    The agent should already exist in the crew class and have a keyword argument `tools`.
    """
    with CrewFile(conf.PATH / ENTRYPOINT) as crew_file:
        crew_file.add_agent_tools(agent_name, tool)


def remove_tool(tool: ToolConfig, agent_name: str):
    """
    Remove a tool from the CrewAI framework for the specified agent.
    """
    with CrewFile(conf.PATH / ENTRYPOINT) as crew_file:
        crew_file.remove_agent_tools(agent_name, tool)


def wrap_tool(tool_func: Callable) -> Callable:
    """
    Wrap a tool function with framework-specific functionality.
    """
    try:
        from crewai.tools import tool as _crewai_tool_decorator
    except ImportError:
        raise ValidationError("Could not import `crewai`. Is this an AgentStack CrewAI project?")

    return _crewai_tool_decorator(tool_func)


def get_graph() -> list[graph.Edge]:
    """Get the graph of the user's project."""
    log.debug("CrewAI does not support graph generation.")
    return []
