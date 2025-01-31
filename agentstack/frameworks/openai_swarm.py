from typing import Optional, Any, Callable
from pathlib import Path
import ast
from agentstack import conf, log
from agentstack.exceptions import ValidationError
from agentstack.generation import InsertionPoint
from agentstack._tools import ToolConfig
from agentstack.tasks import TaskConfig
from agentstack.agents import AgentConfig
from agentstack.generation import asttools
from agentstack import graph


NAME: str = "OpenAI Swarm"
ENTRYPOINT: Path = Path('src/stack.py')


class SwarmFile(asttools.File):
    """
    Parses and manipulates the entrypoint file.
    All AST interactions should happen within the methods of this class.
    """

    def get_base_class(self) -> ast.ClassDef:
        """
        A base class is the first class inside of the file that follows the
        naming convention: `<FooBar>Stack`
        """
        try:
            return asttools.find_class_with_regex(self.tree, r'\w+Stack$')[0]
        except IndexError:
            raise ValidationError(f"`<FooBar>Stack` class not found in {ENTRYPOINT}")

    def get_run_method(self) -> ast.FunctionDef:
        """A method named `run`."""
        try:
            base_class = self.get_base_class()
            node = asttools.find_method_in_class(base_class, 'run')[0]
            assert 'inputs' in (arg.arg for arg in node.args.args)
            return node
        except IndexError:
            raise ValidationError(f"`run` method not found in `{base_class.name} class in {ENTRYPOINT}.")
        except AssertionError:
            raise ValidationError(
                f"Method `run` of `{base_class.name}` must accept `inputs` as a keyword argument."
            )

    def get_task_methods(self) -> list[ast.FunctionDef]:
        """A `task` method is a method decorated with `@task`."""
        return asttools.find_decorated_method_in_class(self.get_base_class(), 'task')

    def add_task_method(self, task: TaskConfig):
        """Add a new task method to the entrypoint."""
        task_methods = self.get_task_methods()
        if task_methods:
            # Add after the existing task methods
            _, pos = self.get_node_range(task_methods[-1])
        else:
            # Add before the `main` method
            main_method = self.get_run_method()
            pos, _ = self.get_node_range(main_method)

        code = f"""    @agentstack.task
    def {task.name}(self, messages: list[str] = []) -> Agent:
        task_config = agentstack.get_task('{task.name}')
        agent = getattr(self, task_config.agent)
        messages = [
            *messages, 
            task_config.prompt, 
        ]
        return agent(messages)"""

        if not self.source[:pos].endswith('\n'):
            code = '\n\n' + code
        if not self.source[pos:].startswith('\n'):
            code += '\n\n'
        self.edit_node_range(pos, pos, code)
        
        # add a new task to the last agent in the stack
        existing_agent_methods = self.get_agent_methods()
        if not len(existing_agent_methods):
            return  # no agents to update

    def get_agent_methods(self) -> list[ast.FunctionDef]:
        """An `agent` method is a method decorated with `@agent`."""
        return asttools.find_decorated_method_in_class(self.get_base_class(), 'agent')

    def add_agent_method(self, agent: AgentConfig) -> None:
        """Add a new agent method to the entrypoint."""
        agent_methods = self.get_agent_methods()
        if agent_methods:
            # Add after the existing agent methods
            _, pos = self.get_node_range(agent_methods[-1])
        else:
            # Add before the `main` method
            main_method = self.get_run_method()
            pos, _ = self.get_node_range(main_method)

        code = f"""    @agentstack.agent
    def {agent.name}(self, messages: list[str] = []) -> Agent:
        agent_config = agentstack.get_agent('{agent.name}')
        messages = [
            agent_config.prompt,
            *messages,
        ]
        return Agent(
            name=agent_config.name, 
            model=agent_config.model, 
            instructions='\\n'.join(messages),
            functions=[],
        )"""

        if not self.source[:pos].endswith('\n'):
            code = '\n\n' + code
        if not self.source[pos:].startswith('\n'):
            code += '\n\n'
        self.edit_node_range(pos, pos, code)

    def get_agent_tools(self, agent_name: str) -> ast.List:
        """Get the tools used by an agent as AST nodes."""
        method = asttools.find_method(self.get_agent_methods(), agent_name)
        if method is None:
            raise ValidationError(f"Agent method `{agent_name}` does not exist in {ENTRYPOINT}")

        # find the `functions` keyword argument to `Agent` inside method
        try:
            agent_init = asttools.find_method_calls(method, 'Agent')[0]
        except IndexError:
            raise ValidationError(f"Agent method `{agent_name}` does not instantiate `Agent` in {ENTRYPOINT}")

        tools_kwarg = asttools.find_kwarg_in_method_call(agent_init, 'functions')

        if not tools_kwarg:
            raise ValidationError(
                f"`@agent` method `{agent_name}` does not have a keyword argument `functions` in {ENTRYPOINT}"
            )

        if not isinstance(tools_kwarg.value, ast.List):
            raise ValidationError(
                f"`@agent` method `{agent_name}` has a non-list value for the `functions` kwarg in {ENTRYPOINT}"
            )

        return tools_kwarg.value

    def get_agent_tool_nodes(self, agent_name: str) -> list[ast.Starred]:
        """
        Get a list of all ast nodes that define agentstack tools used by the agent.
        """
        agent_tools_node = self.get_agent_tools(agent_name)
        return asttools.find_tool_nodes(agent_tools_node)

    def get_agent_tool_names(self, agent_name: str) -> list[str]:
        """Get a list of all tools used by the agent."""
        tool_names: list[str] = []
        for node in self.get_agent_tool_nodes(agent_name):
            # ignore type checking here since `get_agent_tool_nodes` is exhaustive
            tool_names.append(node.value.slice.value)  # type: ignore[attr-defined]
        return tool_names

    def add_agent_tools(self, agent_name: str, tool: ToolConfig) -> None:
        """Add new tools to be used by an agent."""
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

    def remove_agent_tools(self, agent_name: str, tool: ToolConfig) -> None:
        """Remove tools from an agent belonging to `tool`."""
        existing_node: ast.List = self.get_agent_tools(agent_name)
        start, end = self.get_node_range(existing_node)

        # modify the existing node to remove any matching tools
        for node in self.get_agent_tool_nodes(agent_name):
            # ignore type checking here since `get_agent_tool_nodes` is exhaustive
            if tool.name == node.value.slice.value:  # type: ignore[attr-defined]
                existing_node.elts.remove(node)

        self.edit_node_range(start, end, existing_node)


def validate_project() -> None:
    """
    Validate that the project is ready to run.
    Raises an `agentstack.ValidationError` if the project is not valid.
    """
    try:
        entrypoint = SwarmFile(conf.PATH / ENTRYPOINT)
    except ValidationError as e:
        raise e

    # A valid project must have a class in the entrypoint file
    try:
        class_node = entrypoint.get_base_class()
    except ValidationError as e:
        raise e

    # The class must have a `run` method
    try:
        entrypoint.get_run_method()
    except ValidationError as e:
        raise e

    # The class must have one or more methods decorated with `@task`
    if len(entrypoint.get_task_methods()) < 1:
        raise ValidationError(
            f"`@task` decorated method not found in `{class_node.name}` class in {ENTRYPOINT}.\n"
            "Create a new task using `agentstack generate task <task_name>`."
        )

    # The class must have one or more methods decorated with `@agent`
    if len(entrypoint.get_agent_methods()) < 1:
        raise ValidationError(
            f"`@agent` decorated method not found in `{class_node.name}` class in {ENTRYPOINT}.\n"
            "Create a new agent using `agentstack generate agent <agent_name>`."
        )


def parse_llm(llm: str) -> tuple[str, str]:
    """
    Parse the llm string into a tuple of `provider` and `model`.
    """
    provider, model = llm.split('/')
    return provider, model


def get_task_method_names() -> list[str]:
    """
    Get a list of task names (methods with an @task decorator).
    """
    entrypoint = SwarmFile(conf.PATH / ENTRYPOINT)
    return [method.name for method in entrypoint.get_task_methods()]


def add_task(task: TaskConfig, position: Optional['InsertionPoint'] = None) -> None:
    """
    Add a task method to the entrypoint.
    """
    if position is not None:
        raise NotImplementedError(f"Task insertion points are not supported in {NAME}.")

    with SwarmFile(conf.PATH / ENTRYPOINT) as entrypoint:
        entrypoint.add_task_method(task)


def get_agent_method_names() -> list[str]:
    """
    Get a list of agent names (methods with an @agent decorator).
    """
    entrypoint = SwarmFile(conf.PATH / ENTRYPOINT)
    return [method.name for method in entrypoint.get_agent_methods()]


def get_agent_tool_names(agent_name: str) -> list[Any]:
    """
    Get a list of tools used by an agent.
    """
    with SwarmFile(conf.PATH / ENTRYPOINT) as entrypoint:
        return entrypoint.get_agent_tool_names(agent_name)


def add_agent(agent: AgentConfig, position: Optional[InsertionPoint] = None) -> None:
    """
    Add an agent method to the entrypoint.
    """
    if position is not None:
        raise NotImplementedError(f"Agent insertion points are not supported in {NAME}.")

    with SwarmFile(conf.PATH / ENTRYPOINT) as entrypoint:
        entrypoint.add_agent_method(agent)


def add_tool(tool: ToolConfig, agent_name: str):
    """
    Add a tool to the entrypoint for the specified agent.
    """
    with SwarmFile(conf.PATH / ENTRYPOINT) as entrypoint:
        entrypoint.add_agent_tools(agent_name, tool)


def remove_tool(tool: ToolConfig, agent_name: str):
    """
    Remove a tool from the entrypoint for the specified agent.
    """
    with SwarmFile(conf.PATH / ENTRYPOINT) as entrypoint:
        entrypoint.remove_agent_tools(agent_name, tool)


def wrap_tool(tool_func: Callable) -> Callable:
    """
    Wrap a tool function with framework-specific functionality.
    """
    # Swarm agents accept raw functions as tools, so no wrapping is needed.
    return tool_func


def get_graph() -> list[graph.Edge]:
    """Get the graph of the user's project."""
    log.debug(f"{NAME} does not support graph generation.")
    return []
