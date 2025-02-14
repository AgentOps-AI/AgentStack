from functools import wraps
from typing import Optional, Union, Callable, Any

from pathlib import Path
import ast
from agentstack import conf, log
from agentstack import packaging
from agentstack.exceptions import ValidationError
from agentstack.generation import asttools, InsertionPoint
from agentstack.frameworks import Provider, BaseEntrypointFile
from agentstack._tools import ToolConfig
from agentstack.agents import AgentConfig, get_all_agent_names
from agentstack.tasks import TaskConfig, get_all_task_names
from agentstack import graph


NAME: str = "LangGraph"
ENTRYPOINT: Path = Path('src/graph.py')

GRAPH_NODE_START = 'START'
GRAPH_NODE_END = 'END'
GRAPH_NODE_TOOLS = 'tools'  # references the `ToolNode` instance
GRAPH_NODE_TOOLS_CONDITION = 'tools_condition'
GRAPH_NODES_SPECIAL = (
    GRAPH_NODE_START,
    GRAPH_NODE_END,
    GRAPH_NODE_TOOLS_CONDITION,
)

PROVIDERS = {
    'openai': Provider(
        class_name='ChatOpenAI',
        module_name='langchain_openai',
        dependencies=['langchain-openai>=0.3.0'],
    ),
    'deepseek': Provider(
        class_name='ChatDeepSeek',
        module_name='langchain_deepseek_official',
        dependencies=['langchain-deepseek-official>=0.1.0'],
    ),
    'anthropic': Provider(
        class_name='ChatAnthropic',
        module_name='langchain_anthropic',
        dependencies=['langchain-anthropic>=0.3.1'],
    ),
    'google': Provider(
        class_name='ChatGoogleGenerativeAI',
        module_name='langchain_google_genai',
        dependencies=['langchain-google-genai>=2.0.8'],
    ),
    'huggingface': Provider(
        class_name='ChatHuggingFace',
        module_name='langchain_huggingface',
        dependencies=['langchain-huggingface'],
    ),
    'microsoft': Provider(
        class_name='AzureChatOpenAI',
        module_name='langchain_openai',
        dependencies=['langchain-openai'],
    ),
    'mistral': Provider(
        class_name='ChatMistralAI',
        module_name='langchain_mistralai.chat_models',
        dependencies=['langchain-mistralai'],
    ),
    'ollama': Provider(
        class_name='ChatOllama',
        module_name='langchain_ollama.chat_models',
        dependencies=['langchain-ollama'],
    ),
    'groq': Provider(
        class_name='ChatGroq',
        module_name='langchain_groq',
        dependencies=['langchain-groq'],
    ),
}


class LangGraphFile(BaseEntrypointFile):
    """
    Parses and manipulates the LangGraph entrypoint file.
    """

    base_class_pattern: str = r'\w+Graph$'

    def get_new_task_method(self, task: TaskConfig) -> str:
        return f"""    @agentstack.task
    def {task.name}(self, state: State):
        task_config = agentstack.get_task('{task.name}')
        messages = ChatPromptTemplate.from_messages([
            ("user", task_config.prompt), 
        ])
        messages = messages.format_messages(**state['inputs'])
        return {{'messages': messages + state['messages']}}"""

    def get_new_agent_method(self, agent: AgentConfig) -> str:
        assert agent.provider in PROVIDERS.keys()  # this gets validated in `add_agent`
        agent_class_name = PROVIDERS[agent.provider].class_name
        return f"""    @agentstack.agent
    def {agent.name}(self, state: State):
        agent_config = agentstack.get_agent('{agent.name}')
        messages = ChatPromptTemplate.from_messages([
            ("user", agent_config.prompt), 
        ])
        messages = messages.format_messages(**state['inputs'])
        agent = {agent_class_name}(model=agent_config.model)
        response = agent.invoke(
            messages + state['messages'],
        )
        return {{'messages': [response, ]}}"""

    def get_global_tools(self) -> ast.List:
        try:
            method = asttools.find_method_calls(self.get_run_method(), 'ToolNode')[0]
        except IndexError:
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
        Get the list of tools used by an agent as an AST List node.

        Tool definitions are inside of the methods marked with an `@agent` decorator.
        The method `bind_tools` is called with a list of tools to bind to the agent.
        """
        method = asttools.find_method(self.get_agent_methods(), agent_name)
        if method is None:
            raise ValidationError(f"Agent method `{agent_name}` does not exist in {ENTRYPOINT}")

        # find the `bind_tools` method call
        try:
            bind_tools = asttools.find_method_calls(method, 'bind_tools')[0]
        except IndexError:
            raise ValidationError(f"Method `{agent_name}` does not call `bind_tools` in {ENTRYPOINT}")

        try:
            assert isinstance(bind_tools.args[0], ast.List)
            tools_list: ast.List = bind_tools.args[0]
        except (IndexError, AssertionError):
            raise ValidationError(
                f"Method `{agent_name}` does not pass a list to `bind_tools` in {ENTRYPOINT}"
            )

        return tools_list

    def add_agent_tools(self, agent_name: str, tool: ToolConfig):
        """
        Add new tools to be used by an agent to the agent's tool list and the
        global ToolNode list.
        """
        method = asttools.find_method(self.get_agent_methods(), agent_name)
        if method is None:
            raise ValidationError(f"Agent method `{agent_name}` does not exist in {ENTRYPOINT}")

        try:
            bind_tools = asttools.find_method_calls(method, 'bind_tools')[0]
        except IndexError:
            # create node for the `bind_tools` method call after the Agent instantiation
            # we add this when we actually add the first tool to the Agent, since
            # passing an empty list to `bind_tools` throws an error.
            agent_conf = AgentConfig(agent_name)
            agent_class_name = PROVIDERS[agent_conf.provider].class_name
            agent_instantiation = asttools.find_method_calls(method, agent_class_name)[0]
            _, pos = self.get_node_range(agent_instantiation)
            # TODO we could dynamically find the Agent variable name
            code = """
        agent = agent.bind_tools([])"""
            self.edit_node_range(pos, pos, code)

        # add the tool to the agent's tools list
        super().add_agent_tools(agent_name, tool)

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
        # remove the tool from the agent's tools list
        super().remove_agent_tools(agent_name, tool)

        # remove the tool from the global tools list
        existing_global_node: ast.List = self.get_global_tools()
        global_start, global_end = self.get_node_range(existing_global_node)
        for node in self.get_global_tool_nodes():
            if tool.name == node.value.slice.value:  # type: ignore[attr-defined]
                existing_global_node.elts.remove(node)
        self.edit_node_range(global_start, global_end, existing_global_node)

    def get_graph_nodes(self) -> list[ast.Call]:
        """Get all of the AST Call nodes that create the graph nodes."""

        def _get_node_name(node: ast.expr) -> str:
            if isinstance(node, ast.Str):
                return node.s
            raise ValidationError(f"Could not determine name of node `{node}` in {ENTRYPOINT}")

        nodes = asttools.find_method_calls(self.get_run_method(), 'add_node')
        for node in nodes:
            source, target = node.args
            source_name = _get_node_name(source)
            # target_name = _get_node_name(target)
            if source_name == GRAPH_NODE_TOOLS:  # TODO this is a bit brittle
                nodes.remove(node)
            # if target_name == GRAPH_NODE_TOOLS:
            #     nodes.remove(node)
        return nodes

    def get_graph_edge_nodes(self) -> list[ast.Call]:
        """Get all of the AST Call nodes that create the graph edges."""
        # TODO do we need to exclude the tools?
        nodes = asttools.find_method_calls(self.get_run_method(), 'add_edge')
        for node in nodes:
            if not len(node.args) == 2:
                raise ValidationError(f"Invalid `add_edge` call in {ENTRYPOINT}")

            source, target = node.args
            if isinstance(source, ast.Str) and source.s == GRAPH_NODE_TOOLS:
                nodes.remove(node)
            if isinstance(target, ast.Str) and target.s == GRAPH_NODE_TOOLS:
                nodes.remove(node)
        return nodes

    def get_graph(self) -> list[graph.Edge]:
        """Get all of the edge definitions from the graph configuration."""
        graph_edges = self.get_graph_edge_nodes()

        def _get_type(name: str) -> graph.NodeType:
            if name in GRAPH_NODES_SPECIAL:
                return graph.NodeType.SPECIAL
            if name == GRAPH_NODE_TOOLS:
                return graph.NodeType.TOOLS
            if name in get_all_agent_names():
                return graph.NodeType.AGENT
            if name in get_all_task_names():
                return graph.NodeType.TASK
            raise ValidationError(f"Could not determine type of node `{name}` in {ENTRYPOINT}")

        def _get_node(node: ast.expr) -> graph.Node:
            if isinstance(node, ast.Str):  # a string
                return graph.Node(name=node.s, type=_get_type(node.s))
            if isinstance(node, ast.Name):  # a variable
                return graph.Node(name=node.id, type=_get_type(node.id))
            raise ValidationError(f"Could not determine type of node `{node}` in {ENTRYPOINT}")

        edges = []
        for edge in graph_edges:
            source, target = edge.args
            edges.append(
                graph.Edge(
                    source=_get_node(source),
                    target=_get_node(target),
                )
            )
        return edges

    def add_graph_edge(self, edge: graph.Edge):
        """Add a new edge to the graph configuration."""
        existing_edges: list[ast.Call] = self.get_graph_edge_nodes()
        if len(existing_edges):  # add the new edge after the last existing edge
            _, end = self.get_node_range(existing_edges[-1])
        else:  # find the instantiation of `StateGraph`
            graph_instance = asttools.find_method_calls(self.get_run_method(), 'StateGraph')[0]
            _, end = self.get_node_range(graph_instance)

        source, target = edge.source.name, edge.target.name
        # wrap the node names in quotes if they are not special nodes
        if edge.source.type != graph.NodeType.SPECIAL:
            source = f'"{source}"'
        if edge.target.type != graph.NodeType.SPECIAL:
            target = f'"{target}"'

        code = f"""
        self.graph.add_edge({source}, {target})"""
        self.edit_node_range(end, end, code)

    def add_conditional_edge(self, edge: graph.Edge):
        """Add a new conditional edge to the graph configuration."""
        existing_edges: list[ast.Call] = self.get_graph_edge_nodes()
        if len(existing_edges):
            _, end = self.get_node_range(existing_edges[-1])
        else:
            graph_instance = asttools.find_method_calls(self.get_run_method(), 'StateGraph')[0]
            _, end = self.get_node_range(graph_instance)

        source, target = edge.source.name, edge.target.name
        # wrap the node names in quotes if they are not special nodes
        if edge.source.type != graph.NodeType.SPECIAL:
            source = f'"{source}"'
        if edge.target.type != graph.NodeType.SPECIAL:
            target = f'"{target}"'

        code = f"""
        self.graph.add_conditional_edges({source}, {target})"""
        self.edit_node_range(end, end, code)

    def remove_graph_edge(self, edge: graph.Edge):
        """Remove an edge from the graph configuration."""

        def _get_node_name(node: ast.expr) -> str:
            if isinstance(node, ast.Str):
                return node.s
            if isinstance(node, ast.Name):
                return node.id
            raise ValidationError(f"Could not determine name of node `{node}` in {ENTRYPOINT}")

        existing_edges: list[ast.Call] = self.get_graph_edge_nodes()
        for edge_node in existing_edges:
            source_node, target_node = edge_node.args
            source, target = _get_node_name(source_node), _get_node_name(target_node)
            if source == edge.source.name and target == edge.target.name:
                return self.remove_node(edge_node)

        raise ValidationError(
            f"Graph `add_edge({edge.source.name}, {edge.target.name})` not found for removal in {ENTRYPOINT}"
        )

    def add_graph_node(self, node_config: Union[AgentConfig, TaskConfig]):
        """Add a new node to the graph configuration."""
        # this adds the node to the graph and relies on an existing edge
        existing_nodes: list[ast.Call] = self.get_graph_nodes()
        if len(existing_nodes):  # add the new node after the last existing node
            _, end = self.get_node_range(existing_nodes[-1])
        else:  # find the instantiation of `StateGraph`
            graph_instance = asttools.find_method_calls(self.get_run_method(), 'StateGraph')[0]
            _, end = self.get_node_range(graph_instance)

        # node is always either an Agent or a Task so we can make this assumption
        code = f"""
        self.graph.add_node("{node_config.name}", self.{node_config.name})"""
        self.edit_node_range(end, end, code)

    def remove_graph_node(self, node_config: Union[AgentConfig, TaskConfig]):
        """Remove a node and it's edges from the graph configuration."""

        # this just removes the node, use `remove_graph_edge` to remove the edges
        def _get_node_name(node: ast.expr) -> str:
            if isinstance(node, ast.Str):
                return node.s
            raise ValidationError(f"Could not determine name of node `{node}` in {ENTRYPOINT}")

        existing_nodes: list[ast.Call] = self.get_graph_nodes()
        for node in existing_nodes:
            source_node, target_node = node.args
            source = _get_node_name(source_node)
            if source == node_config.name:
                return self.remove_node(node)

        raise ValidationError(f"Node `{node_config.name}` not found in {ENTRYPOINT}")


def get_entrypoint() -> LangGraphFile:
    """Get the LangGraph entrypoint file."""
    return LangGraphFile(conf.PATH / ENTRYPOINT)


def validate_project() -> None:
    """
    Validate that a langgraph project is ready to run.
    Raises an `agentstack.ValidationError` if the project is not valid.
    """
    return  # No additional validation needed


def add_task(task: TaskConfig, position: Optional[InsertionPoint] = None) -> None:
    """
    Add a task method to the LangGraph entrypoint.
    """
    if position is None:
        position = InsertionPoint.END
    if not position in (InsertionPoint.BEGIN, InsertionPoint.END):
        raise ValidationError(f"Invalid insertion point: {position}")

    with get_entrypoint() as entrypoint:
        entrypoint.add_task_method(task)
        entrypoint.add_graph_node(task)

        existing_nodes = entrypoint.get_graph()
        if position == InsertionPoint.END:
            # replace the existing END node with the new agent, and insert the
            # previous END node's source as the new agent's source
            prev_source = None
            for node in existing_nodes:
                source, target = node.source, node.target
                if target.type == graph.NodeType.SPECIAL and target.name == GRAPH_NODE_END:
                    prev_source = source
                    entrypoint.remove_graph_edge(node)
                    break

            if prev_source:
                entrypoint.add_graph_edge(
                    graph.Edge(
                        source=graph.Node(name=prev_source.name, type=prev_source.type),
                        target=graph.Node(name=task.name, type=graph.NodeType.TASK),
                    )
                )
            else:
                log.warning(f"Could not find {GRAPH_NODE_END} node to replace in {ENTRYPOINT}")
            entrypoint.add_graph_edge(
                graph.Edge(
                    source=graph.Node(name=task.name, type=graph.NodeType.TASK),
                    target=graph.Node(name=GRAPH_NODE_END, type=graph.NodeType.SPECIAL),
                )
            )
        elif position == InsertionPoint.BEGIN:
            # replace the existing START node with the new agent, and insert the
            # new agent as the source of the previous START node
            # TODO this places the new edges at the end of the graph definition,
            # so while it is functionally correct, it is not visually intuitive
            prev_target = None
            for node in existing_nodes:
                source, target = node.source, node.target
                if source.type == graph.NodeType.SPECIAL and source.name == GRAPH_NODE_START:
                    prev_target = target
                    entrypoint.remove_graph_edge(node)
                    break

            entrypoint.add_graph_edge(
                graph.Edge(
                    source=graph.Node(name=GRAPH_NODE_START, type=graph.NodeType.SPECIAL),
                    target=graph.Node(name=task.name, type=graph.NodeType.TASK),
                )
            )
            if prev_target:
                entrypoint.add_graph_edge(
                    graph.Edge(
                        source=graph.Node(name=task.name, type=graph.NodeType.TASK),
                        target=graph.Node(name=prev_target.name, type=prev_target.type),
                    )
                )
            else:
                log.warning(f"Could not find {GRAPH_NODE_START} node to replace in {ENTRYPOINT}")


def add_agent(agent: AgentConfig, position: Optional[InsertionPoint] = None) -> None:
    """
    Add an agent method to the LangGraph entrypoint.
    """
    if position is None:
        position = InsertionPoint.END
    if not position in (InsertionPoint.BEGIN, InsertionPoint.END):
        raise ValidationError(f"Invalid insertion point: {position}")

    # individual LLM providers rely on additional dependencies, install them
    try:
        provider = PROVIDERS[agent.provider]
        provider.install_dependencies()
    except KeyError:
        raise ValidationError(
            f"{NAME} provider '{agent.provider}' has not been implemented. "
            f"AgentStack currently supports: {', '.join(PROVIDERS.keys())} "
        )

    with get_entrypoint() as entrypoint:
        # also include an import statement for the LLM provider
        if not entrypoint.get_import(provider.module_name, provider.class_name):
            entrypoint.add_import(provider.module_name, provider.class_name)

        entrypoint.add_agent_method(agent)
        entrypoint.add_graph_node(agent)

        # add graph edge to get back from the `tools` to the Agent
        entrypoint.add_graph_edge(
            graph.Edge(
                source=graph.Node(name=GRAPH_NODE_TOOLS, type=graph.NodeType.TOOLS),
                target=graph.Node(name=agent.name, type=graph.NodeType.AGENT),
            )
        )
        # add conditional edge for `tools_condition`
        entrypoint.add_conditional_edge(
            graph.Edge(
                source=graph.Node(name=agent.name, type=graph.NodeType.AGENT),
                target=graph.Node(name=GRAPH_NODE_TOOLS_CONDITION, type=graph.NodeType.SPECIAL),
            )
        )

        existing_nodes = entrypoint.get_graph()
        if position == InsertionPoint.END:
            # replace the existing END node with the new agent, and insert the
            # previous END node's source as the new agent's source
            prev_source = None
            for node in existing_nodes:
                source, target = node.source, node.target
                if target.type == graph.NodeType.SPECIAL and target.name == GRAPH_NODE_END:
                    prev_source = source
                    entrypoint.remove_graph_edge(node)
                    break

            if prev_source:
                entrypoint.add_graph_edge(
                    graph.Edge(
                        source=graph.Node(name=prev_source.name, type=prev_source.type),
                        target=graph.Node(name=agent.name, type=graph.NodeType.AGENT),
                    )
                )
            else:
                log.warning(f"Could not find {GRAPH_NODE_END} node to replace in {ENTRYPOINT}")
            entrypoint.add_graph_edge(
                graph.Edge(
                    source=graph.Node(name=agent.name, type=graph.NodeType.AGENT),
                    target=graph.Node(name=GRAPH_NODE_END, type=graph.NodeType.SPECIAL),
                )
            )
        elif position == InsertionPoint.BEGIN:
            # replace the existing START node with the new agent, and insert the
            # new agent as the source of the previous START node
            # TODO this places the new edges at the end of the graph definition,
            # so while it is functionally correct, it is not visually intuitive
            prev_target = None
            for node in existing_nodes:
                source, target = node.source, node.target
                if source.type == graph.NodeType.SPECIAL and source.name == GRAPH_NODE_START:
                    prev_target = target
                    entrypoint.remove_graph_edge(node)
                    break

            entrypoint.add_graph_edge(
                graph.Edge(
                    source=graph.Node(name=GRAPH_NODE_START, type=graph.NodeType.SPECIAL),
                    target=graph.Node(name=agent.name, type=graph.NodeType.AGENT),
                )
            )
            if prev_target:
                entrypoint.add_graph_edge(
                    graph.Edge(
                        source=graph.Node(name=agent.name, type=graph.NodeType.AGENT),
                        target=graph.Node(name=prev_target.name, type=prev_target.type),
                    )
                )
            else:
                log.warning(f"Could not find {GRAPH_NODE_START} node to replace in {ENTRYPOINT}")


def add_tool(tool: ToolConfig, agent_name: str):
    """
    Add a tool to the LangGraph entrypoint for the specified agent.
    The agent should already exist in the base class and have a `bind_tools` method call.
    """
    with get_entrypoint() as entrypoint:
        entrypoint.add_agent_tools(agent_name, tool)


def remove_tool(tool: ToolConfig, agent_name: str):
    """
    Remove a tool from the CrewAI framework for the specified agent.
    """
    with get_entrypoint() as entrypoint:
        entrypoint.remove_agent_tools(agent_name, tool)


def wrap_tool(tool_func: Callable) -> Callable:
    """
    Wrap a tool function with framework-specific functionality.
    """
    # LangGraph accepts bare functions as tools, so we don't need to do anything here.
    return tool_func


def get_graph() -> list[graph.Edge]:
    """Get the graph structure of the project."""
    return get_entrypoint().get_graph()
