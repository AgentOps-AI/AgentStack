from typing import Optional, Any
from pathlib import Path
import ast
from agentstack import conf
from agentstack.exceptions import ValidationError
from agentstack.generation import asttools
from agentstack._tools import ToolConfig
from agentstack.agents import AgentConfig
from agentstack.tasks import TaskConfig

ENTRYPOINT: Path = Path('src/graph.py')


class LangGraphFile(asttools.File):
    """
    Parses and manipulates the LangGraph entrypoint file. 
    """
    def get_base_class(self) -> ast.ClassDef:
        """
        A base class is the first class inside of the file that follows the 
        naming convention: `<FooBar>Graph`
        """
        try:
            return asttools.find_class_with_regex(self.tree, r'\w+Graph$')[0]
        except IndexError:
            raise ValidationError(f"`<FooBar>Graph` class not found in {ENTRYPOINT}")

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
            raise ValidationError(f"Method `run` of `{base_class.name}` must accept `inputs` as a keyword argument.")

    def get_task_methods(self) -> list[ast.FunctionDef]:
        """A `task` method is a method decorated with `@task`."""
        return asttools.find_decorated_method_in_class(self.get_base_class(), 'task')

    def add_task_method(self, task: TaskConfig):
        """Add a new task method to the LangGraph entrypoint."""
        task_methods = self.get_task_methods()
        if task_methods:
            # Add after the existing task methods
            _, pos = self.get_node_range(task_methods[-1])
        else:
            # Add before the `main` method
            main_method = self.get_run_method()
            pos, _ = self.get_node_range(main_method)

        code = f"""    @agentstack.task
    def {task.name}(self, state: State):
        task_config = agentstack.get_task('{task.name}')
        messages = ChatPromptTemplate.from_messages([
            ("user", task_config.prompt), 
        ])
        messages = messages.format_messages(**state['inputs'])
        return {{'messages': messages + state['messages']}}"""
        
        if not self.source[:pos].endswith('\n'):
            code = '\n\n' + code
        if not self.source[pos:].startswith('\n'):
            code += '\n\n'
        self.edit_node_range(pos, pos, code)

    def get_agent_methods(self) -> list[ast.FunctionDef]:
        """An `agent` method is a method decorated with `@agent`."""
        return asttools.find_decorated_method_in_class(self.get_base_class(), 'agent')

    def get_agent_provider_class_name(self, provider: str) -> str:
        """LangGraph uses separate classes for each LLM provider."""
        # TODO import supporting classes into the entrypoint
        # TODO providers may need dependencies to be installed
        provider_class = {
            'openai': 'ChatOpenAI',
            'anthropic': 'ChatAnthropic',
        }
        try:
            return provider_class[provider]
        except KeyError:
            raise ValidationError(
                f"LangGraph provider '{provider}' has not been implemented. "
                f"AgentStack currently supports: {', '.join(provider_class.keys())} "
            )

    def add_agent_method(self, agent: AgentConfig):
        """Add a new agent method to the LangGraph entrypoint."""
        agent_methods = self.get_agent_methods()
        if agent_methods:
            # Add after the existing agent methods
            _, pos = self.get_node_range(agent_methods[-1])
        else:
            # Add before the `main` method
            main_method = self.get_run_method()
            pos, _ = self.get_node_range(main_method)

        agent_class_name = self.get_agent_provider_class_name(agent.provider)
        code = f"""    @agentstack.agent
    def {agent.name}(self, state: State) -> Agent:
        agent_config = agentstack.get_agent('{agent.name}')
        messages = ChatPromptTemplate.from_messages([
            ("user", agent_config.prompt), 
        ])
        messages = messages.format_messages(**state['inputs'])
        agent = {agent_class_name}(model=agent_config.model)
        agent = agent.bind_tools([])
        response = agent.invoke(
            messages + state['messages'],
        )
        return {{'messages': [response, ]}}"""
        
        if not self.source[:pos].endswith('\n'):
            code = '\n\n' + code
        if not self.source[pos:].startswith('\n'):
            code += '\n\n'
        self.edit_node_range(pos, pos, code)
    
    def get_global_tools(self) -> ast.List:
        method = asttools.find_method_call(self.get_run_method(), 'ToolNode')
        if method is None:
            raise ValidationError(f"`run` method does not instantiate `ToolNode` in {ENTRYPOINT}")
        
        try:
            assert isinstance(method.args[0], ast.List)
            tools_list: ast.List = method.args[0]
        except (IndexError, AssertionError):
            raise ValidationError(f"`run` method does not pass a list to `ToolNode` in {ENTRYPOINT}")
        return tools_list
    
    def get_global_tool_nodes(self) -> list[ast.Starred]:
        """
        Get a list of all ast nodes that define global tools used by the project.
        """
        global_tools_node = self.get_global_tools()
        return asttools.find_tool_nodes(global_tools_node)
    
    def get_global_tool_names(self) -> list[str]:
        """
        Get a list of all tools used by the project.

        Tools are identified by the item name of an `agentstack.tools` attribute node.
        """
        tool_names: list[str] = []
        for node in self.get_global_tool_nodes():
            tool_names.append(node.value.slice.value)  # type: ignore[attr-defined]
        return tool_names
    
    def get_agent_tools(self, agent_name: str) -> ast.List:
        """
        Get the tools used by an agent as AST nodes.

        Tool definitions are inside of the methods marked with an `@agent` decorator.
        The method `bind_tools` is called with a list of tools to bind to the agent.
        """
        method = asttools.find_method(self.get_agent_methods(), agent_name)
        if method is None:
            raise ValidationError(f"Agent method `{agent_name}` does not exist in {ENTRYPOINT}")

        # find the `bind_tools` method call
        bind_tools = asttools.find_method_call(method, 'bind_tools')
        if bind_tools is None:
            raise ValidationError(f"Method `{agent_name}` does not call `bind_tools` in {ENTRYPOINT}")

        try:
            assert isinstance(bind_tools.args[0], ast.List)
            tools_list: ast.List = bind_tools.args[0]
        except (IndexError, AssertionError):
            raise ValidationError(f"Method `{agent_name}` does not pass a list to `bind_tools` in {ENTRYPOINT}")
        
        return tools_list
    
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
        Add new tools to be used by an agent to the agent's tool list and the 
        global ToolNode list.
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
        
        # add the tool to the global tools list
        existing_global_node: ast.List = self.get_global_tools()
        existing_global_elts: list[ast.expr] = existing_global_node.elts
        
        new_global_tool_nodes: list[ast.expr] = []
        if not tool.name in self.get_global_tool_names():
            existing_global_elts.append(asttools.create_tool_node(tool.name))
        
        new_global_node = ast.List(elts=existing_global_elts, ctx=ast.Load())
        global_start, global_end = self.get_node_range(existing_global_node)
        self.edit_node_range(global_start, global_end, new_global_node)

    def remove_agent_tools(self, agent_name: str, tool: ToolConfig):
        """
        Remove tools from an agent belonging to `tool` from the agent's tool list
        and the global ToolNode list.
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
        
        # remove the tool from the global tools list
        existing_global_node: ast.List = self.get_global_tools()
        global_start, global_end = self.get_node_range(existing_global_node)
        for node in self.get_global_tool_nodes():
            if tool.name == node.value.slice.value:  # type: ignore[attr-defined]
                existing_global_node.elts.remove(node)
        self.edit_node_range(global_start, global_end, existing_global_node)


def validate_project() -> None:
    """
    Validate that a langgraph project is ready to run.
    Raises an `agentstack.ValidationError` if the project is not valid.
    """
    graph_file = LangGraphFile(conf.PATH / ENTRYPOINT)
    
    # A valid project must have a class in the graph.py file that is named <Foo>Graph.
    # will raise a ValidationError if the class is not found
    class_node = graph_file.get_base_class()
    
    # The base class must implement a method called `run` that accepts `inputs`
    # as a keyword argument. 
    # will raise a ValidationError if the method is not found or does not have the correct signature
    _ = graph_file.get_run_method()

    # The base class must have one or more methods decorated with `@task`
    if len(graph_file.get_task_methods()) < 1:
        raise ValidationError(
            f"`@agentstack.task` decorated method not found in `{class_node.name}` class in {ENTRYPOINT}.\n"
            "Create a new task using `agentstack generate task <task_name>`."
        )

    # The base class must have one or more methods decorated with `@agent`
    if len(graph_file.get_agent_methods()) < 1:
        raise ValidationError(
            f"`@agentstack.agent` decorated method not found in `{class_node.name}` class in {ENTRYPOINT}.\n"
            "Create a new agent using `agentstack generate agent <agent_name>`."
        )


def parse_llm(llm: str) -> tuple[str, str]:
    """
    Parse a language model string into a provider and model.
    LangGraph separates providers and models with a forward slash.
    """
    provider, model = llm.split('/')
    return provider, model


def get_task_names() -> list[str]:
    """
    Get a list of task names (methods with an @task decorator).
    """
    entrypoint = LangGraphFile(conf.PATH / ENTRYPOINT)
    return [method.name for method in entrypoint.get_task_methods()]


def add_task(task: TaskConfig) -> None:
    """
    Add a task method to the LangGraph entrypoint.
    """
    with LangGraphFile(conf.PATH / ENTRYPOINT) as entrypoint:
        entrypoint.add_task_method(task)


def get_agent_names() -> list[str]:
    """
    Get a list of agent names (methods with an @agent decorator).
    """
    entrypoint = LangGraphFile(conf.PATH / ENTRYPOINT)
    return [method.name for method in entrypoint.get_agent_methods()]


def get_agent_tool_names(agent_name: str) -> list[Any]:
    """
    Get a list of tools used by an agent.
    """
    with LangGraphFile(conf.PATH / ENTRYPOINT) as entrypoint:
        return entrypoint.get_agent_tool_names(agent_name)


def add_agent(agent: AgentConfig) -> None:
    """
    Add an agent method to the LangGraph entrypoint.
    """
    with LangGraphFile(conf.PATH / ENTRYPOINT) as entrypoint:
        entrypoint.add_agent_method(agent)


def add_tool(tool: ToolConfig, agent_name: str):
    """
    Add a tool to the LangGraph entrypoint for the specified agent.
    The agent should already exist in the base class and have a `bind_tools` method call.
    """
    with LangGraphFile(conf.PATH / ENTRYPOINT) as entrypoint:
        entrypoint.add_agent_tools(agent_name, tool)


def remove_tool(tool: ToolConfig, agent_name: str):
    """
    Remove a tool from the CrewAI framework for the specified agent.
    """
    with LangGraphFile(conf.PATH / ENTRYPOINT) as entrypoint:
        entrypoint.remove_agent_tools(agent_name, tool)