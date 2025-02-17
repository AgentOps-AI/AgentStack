from typing import Optional, Union, Protocol, Callable
from types import ModuleType
from abc import ABCMeta, abstractmethod
from importlib import import_module
from dataclasses import dataclass
from pathlib import Path
import ast
from agentstack import conf
from agentstack.exceptions import ValidationError
from agentstack.generation import InsertionPoint
from agentstack.utils import get_framework
from agentstack import packaging
from agentstack.generation import asttools
from agentstack.agents import AgentConfig, get_all_agent_names
from agentstack.tasks import TaskConfig, get_all_task_names
from agentstack._tools import ToolConfig
from agentstack import graph


CREWAI = 'crewai'
LANGGRAPH = 'langgraph'
OPENAI_SWARM = 'openai_swarm'
LLAMAINDEX = 'llamaindex'
SUPPORTED_FRAMEWORKS = [
    CREWAI,
    LANGGRAPH,
    OPENAI_SWARM,
    LLAMAINDEX,
]
ALIASED_FRAMEWORKS = {
    'crew': CREWAI,
}
DEFAULT_FRAMEWORK = CREWAI


@dataclass
class Provider:
    """
    An LLM provider definition.

    Used to install required dependencies and provide attributes for an
    import statement.
    """

    class_name: str  # The class we use to import and run the provider
    module_name: str  # The module we import from
    dependencies: list[str]  # Any dependencies needed for use

    def install_dependencies(self):
        """Install the dependencies for the provider."""
        for dependency in self.dependencies:
            packaging.install(dependency)


class FrameworkModule(Protocol):
    """
    Protocol spec for a framework implementation module.
    """

    ENTRYPOINT: Path
    """
    Relative path to the entrypoint file for the framework in the user's project.
    ie. `src/crewai.py`
    """

    def get_entrypoint(self) -> 'BaseEntrypointFile':
        """
        Get the entrypoint file for the framework.
        """
        ...

    def validate_project(self) -> None:
        """
        Validate that a user's project is ready to run.
        Raises a `ValidationError` if the project is not valid.
        """
        ...

    def add_agent(self, agent: 'AgentConfig', position: Optional[InsertionPoint] = None) -> None:
        """
        Add an agent to the user's project.
        """

    def add_task(self, task: 'TaskConfig', position: Optional[InsertionPoint] = None) -> None:
        """
        Add a task to the user's project.
        """
        ...

    def add_tool(self, tool: ToolConfig, agent_name: str) -> None:
        """
        Add a tool to an agent in the user's project.
        """
        ...

    def remove_tool(self, tool: ToolConfig, agent_name: str) -> None:
        """
        Remove a tool from an agent in user's project.
        """
        ...

    def wrap_tool(self, tool_func: Callable) -> Callable:
        """
        Wrap a tool function with framework-specific functionality.
        """
        ...

    def get_graph(self) -> list[graph.Edge]:
        """
        Get the graph of the user's project.
        """
        ...


class BaseEntrypointFile(asttools.File, metaclass=ABCMeta):
    """
    This handles interactions with a Framework's entrypoint file that are common
    to all frameworks.

    In most cases, we have a base class which contains a `run` method, and
    methods decorated with `@agentstack.task` and `@agentstack.agent`.

    We match the base class with a regex pattern defined as `base_class_pattern`,
    and the `run` method with a method named `run` which accepts `inputs` as a
    keyword argument.

    Usually, it looks something like this:
    ```
    class UserStack:
        @agentstack.task
        def task_name(self):
            ...

        @agentstack.agent
        def agent_name(self):
            ...

        def run(self, inputs: list):
            ...
    ```
    """

    base_class_pattern: str = r'\w+Stack$'
    agent_decorator_name: str = 'agent'
    task_decorator_name: str = 'task'

    def get_import(self, module_name: str, attributes: str) -> Optional[ast.ImportFrom]:
        """
        Return an import statement for a module and class if it exists in the file.
        """
        for node in asttools.get_all_imports(self.tree):
            names_str = ', '.join(alias.name for alias in node.names)
            if node.module == module_name and names_str == attributes:
                return node
        return None

    def add_import(self, module_name: str, attributes: str):
        """
        Add an import statement to the file.
        """
        # add the import after existing imports, or at the beginning of the file
        all_imports = asttools.get_all_imports(self.tree)
        _, end = self.get_node_range(all_imports[-1]) if all_imports else (0, 0)

        code = f"from {module_name} import {attributes}\n"
        if not self.source[:end].endswith('\n'):
            code = '\n' + code

        self.edit_node_range(end, end, code)

    def get_base_class(self) -> ast.ClassDef:
        """
        A base class is the first class inside of the file that follows the
        naming convention: `<FooBar>Graph`
        """
        pattern = self.base_class_pattern
        try:
            return asttools.find_class_with_regex(self.tree, pattern)[0]
        except IndexError:
            raise ValidationError(f"`{pattern}` class not found in {self.filename}")

    def get_run_method(self) -> Union[ast.FunctionDef, ast.AsyncFunctionDef]:
        """A method named `run` in the base class which accepts `inputs` as a keyword argument."""
        try:
            base_class = self.get_base_class()
            node = asttools.find_method_in_class(base_class, 'run')
            assert node
        except AssertionError:
            raise ValidationError(f"`run` method not found in `{base_class.name}` class in {self.filename}.")

        try:
            assert 'inputs' in (arg.arg for arg in node.args.args)
            return node
        except AssertionError:
            raise ValidationError(f"Method `run` of `{base_class.name}` must accept `inputs` as a kwarg.")

    def get_task_methods(self) -> list[ast.FunctionDef]:
        """A `task` method is a method decorated with `@<self.task_decorator_name>`."""
        return asttools.find_decorated_method_in_class(self.get_base_class(), self.task_decorator_name)

    def get_task_method_names(self) -> list[str]:
        """Get a list of task names (methods with an @task decorator)."""
        return [method.name for method in self.get_task_methods()]

    # not marked as abstract because you can override `add_task_method` for more
    # control over adding new task methods if you need to
    def get_new_task_method(self, task: TaskConfig) -> str:
        """Get the content of a new task method."""
        # TODO allow returning `Union[str, ast.AST]`
        raise NotImplementedError("Subclass must implement `get_new_task_method` to support insertion.")

    def add_task_method(self, task: TaskConfig):
        """Add a new task method to the entrypoint."""
        task_methods = self.get_task_methods()
        if task_methods:
            # Add after the existing task methods
            _, pos = self.get_node_range(task_methods[-1])
        else:
            # Add before the `run` method
            pos, _ = self.get_node_range(self.get_run_method())

        self.insert_method(pos, self.get_new_task_method(task))

    def get_agent_methods(self) -> list[ast.FunctionDef]:
        """An `agent` method is a method decorated with `@<self.agent_decorator_name>`."""
        return asttools.find_decorated_method_in_class(self.get_base_class(), self.agent_decorator_name)

    def get_agent_method_names(self) -> list[str]:
        """Get a list of agent names (methods with an @agent decorator)."""
        return [method.name for method in self.get_agent_methods()]

    # not marked as abstract because you can override `add_agent_method` for more
    # control over adding new agent methods if you need to
    def get_new_agent_method(self, agent: AgentConfig) -> str:
        """Get the content of a new agent method."""
        # TODO allow returning `Union[str, ast.AST]`
        raise NotImplementedError("Subclass must implement `get_new_agent_method` to support insertion.")

    def add_agent_method(self, agent: AgentConfig):
        """Add a new agent method to the LangGraph entrypoint."""
        agent_methods = self.get_agent_methods()
        if agent_methods:
            # Add after the existing agent methods
            _, pos = self.get_node_range(agent_methods[-1])
        else:
            # Add before the `run` method
            pos, _ = self.get_node_range(self.get_run_method())

        self.insert_method(pos, self.get_new_agent_method(agent))

    @abstractmethod
    def get_agent_tools(self, agent_name: str) -> ast.List:
        """Get the list of tools used by an agent as an AST List node."""
        ...

    def get_agent_tool_nodes(self, agent_name: str) -> list[ast.Starred]:
        """Get a list of all ast nodes that define agentstack tools used by the agent."""
        agent_tools_node = self.get_agent_tools(agent_name)
        return asttools.find_tool_nodes(agent_tools_node)

    def get_agent_tool_names(self, agent_name: str) -> list[str]:
        """Get a list of all tools used by the agent."""
        # Tools are identified by the item name of an `agentstack.tools` attribute node.
        tool_names: list[str] = []
        for node in self.get_agent_tool_nodes(agent_name):
            # ignore type checking here since `get_agent_tool_nodes` is exhaustive
            tool_names.append(node.value.slice.value)  # type: ignore[attr-defined]
        return tool_names

    def add_agent_tools(self, agent_name: str, tool: ToolConfig):
        """Modify the existing tools list to add a new tool."""
        existing_node: ast.List = self.get_agent_tools(agent_name)
        existing_elts: list[ast.expr] = existing_node.elts

        if not tool.name in self.get_agent_tool_names(agent_name):
            existing_elts.append(asttools.create_tool_node(tool.name))

        new_node = ast.List(elts=existing_elts, ctx=ast.Load())
        start, end = self.get_node_range(existing_node)
        self.edit_node_range(start, end, new_node)

    def remove_agent_tools(self, agent_name: str, tool: ToolConfig):
        """Modify the existing tools list to remove a tool."""
        existing_node: ast.List = self.get_agent_tools(agent_name)
        start, end = self.get_node_range(existing_node)

        # we're referencing the internal node list from two directions here,
        # so it's important that the node tree doesn't get re-parsed in between
        for node in self.get_agent_tool_nodes(agent_name):
            # ignore type checking here since `get_agent_tool_nodes` is exhaustive
            if tool.name == node.value.slice.value:  # type: ignore[attr-defined]
                existing_node.elts.remove(node)

        self.edit_node_range(start, end, existing_node)


def get_framework_module(framework: str) -> FrameworkModule:
    """
    Get the module for a framework.
    """
    try:
        return import_module(f".{framework}", package=__package__)
    except ImportError:
        raise Exception(f"Framework {framework} could not be imported.")


def get_entrypoint_path(framework: str) -> Path:
    """
    Get the path to the entrypoint file for a framework.
    """
    module = get_framework_module(framework)
    return conf.PATH / module.ENTRYPOINT


def validate_project():
    """
    Validate that the user's project is ready to run.
    """
    framework = get_framework()
    entrypoint_path = get_entrypoint_path(framework)
    module = get_framework_module(framework)
    entrypoint = module.get_entrypoint()

    # Run framework-specific validation
    module.validate_project()

    # A valid project must have a base class available
    try:
        class_node = entrypoint.get_base_class()
    except ValidationError as e:
        raise e

    # The base class must have a `run` method.
    try:
        entrypoint.get_run_method()
    except ValidationError as e:
        raise e

    # The class must have one or more task methods.
    if len(entrypoint.get_task_methods()) < 1:
        raise ValidationError(
            f"One or more task methods could not be found on class `{class_node.name}` in {entrypoint_path}.\n"
            "Create a new task using `agentstack generate task <task_name>`."
        )

    # The class must have one or more agent methods.
    if len(entrypoint.get_agent_methods()) < 1:
        raise ValidationError(
            f"One or more agent methods could not be found on class `{class_node.name}` in {entrypoint_path}.\n"
            "Create a new agent using `agentstack generate agent <agent_name>`."
        )

    # Verify that agents defined in agents.yaml are present in the codebase
    agent_method_names = entrypoint.get_agent_method_names()
    for agent_name in get_all_agent_names():
        if agent_name not in agent_method_names:
            raise ValidationError(f"Agent `{agent_name}` defined in agents.yaml but not in {entrypoint_path}")

    # Verify that tasks defined in tasks.yaml are present in the codebase
    task_method_names = entrypoint.get_task_method_names()
    for task_name in get_all_task_names():
        if task_name not in task_method_names:
            raise ValidationError(f"Task `{task_name}` defined in tasks.yaml but not in {entrypoint_path}")


def add_tool(tool: ToolConfig, agent_name: str):
    """
    Add a tool to the user's project.
    The tool will have already been installed in the user's application and have
    all dependencies installed. We're just handling code generation here.
    """
    # since this is a write operation, delegate to the framework impl.
    module = get_framework_module(get_framework())
    return module.add_tool(tool, agent_name)


def remove_tool(tool: ToolConfig, agent_name: str):
    """
    Remove a tool from the user's project.
    """
    # since this is a write operation, delegate to the framework impl.
    module = get_framework_module(get_framework())
    return module.remove_tool(tool, agent_name)


def get_tool_callables(tool_name: str) -> list[Callable]:
    """
    Get a tool by name and return it as a list of framework-native callables.
    """

    # TODO: remove after agentops fixes their issue
    # wrap method with agentops tool event
    def wrap_method(method: Callable) -> Callable:
        from inspect import signature

        original_signature = signature(method)

        def wrapped_method(*args, **kwargs):
            import agentops

            tool_event = agentops.ToolEvent(method.__name__)
            result = method(*args, **kwargs)
            agentops.record(tool_event)
            return result

        # Preserve all original attributes
        wrapped_method.__name__ = method.__name__
        wrapped_method.__doc__ = method.__doc__
        wrapped_method.__module__ = method.__module__
        wrapped_method.__qualname__ = method.__qualname__
        wrapped_method.__annotations__ = getattr(method, '__annotations__', {})
        wrapped_method.__signature__ = original_signature  # type: ignore
        return wrapped_method

    tool_funcs = []
    tool_config = ToolConfig.from_tool_name(tool_name)
    for tool_func_name in tool_config.tools:
        tool_func = getattr(tool_config.module, tool_func_name)

        assert callable(tool_func), f"Tool function {tool_func_name} is not callable."
        assert tool_func.__doc__, f"Tool function {tool_func_name} is missing a docstring."

        # First wrap with agentops
        agentops_wrapped = wrap_method(tool_func)
        # Then apply framework decorators
        framework_wrapped = get_framework_module(get_framework()).wrap_tool(agentops_wrapped)
        tool_funcs.append(framework_wrapped)

    return tool_funcs


def get_agent_method_names() -> list[str]:
    """
    Get a list of agent names in the user's project.
    """
    module = get_framework_module(get_framework())
    entrypoint = module.get_entrypoint()
    return entrypoint.get_agent_method_names()


def get_agent_tool_names(agent_name: str) -> list[str]:
    """
    Get a list of tool names in the user's project for a given agent.
    """
    module = get_framework_module(get_framework())
    entrypoint = module.get_entrypoint()
    return entrypoint.get_agent_tool_names(agent_name)


def add_agent(agent: AgentConfig, position: Optional[InsertionPoint] = None):
    """
    Add an agent to the user's project.
    """
    framework = get_framework()
    module = get_framework_module(framework)

    if agent.name in get_agent_method_names():
        raise ValidationError(f"Agent `{agent.name}` already exists in {get_entrypoint_path(framework)}")

    return module.add_agent(agent, position)


def add_task(task: TaskConfig, position: Optional[InsertionPoint] = None):
    """
    Add a task to the user's project.
    """
    framework = get_framework()
    module = get_framework_module(framework)

    if task.name in get_task_method_names():
        raise ValidationError(f"Task `{task.name}` already exists in {get_entrypoint_path(framework)}")

    return module.add_task(task, position)


def get_task_method_names() -> list[str]:
    """
    Get a list of task names in the user's project.
    """
    module = get_framework_module(get_framework())
    entrypoint = module.get_entrypoint()
    return entrypoint.get_task_method_names()


def get_graph() -> list[graph.Edge]:
    """
    Get the graph of the user's project.
    """
    module = get_framework_module(get_framework())
    return module.get_graph()
