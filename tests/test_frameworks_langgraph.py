import os, sys
import shutil
import unittest
from parameterized import parameterized
from pathlib import Path
import ast
from agentstack import conf
from agentstack.exceptions import ValidationError
from agentstack import frameworks
from agentstack.frameworks.langgraph import ENTRYPOINT, LangGraphFile
from agentstack.agents import AGENTS_FILENAME, AgentConfig
from agentstack.tasks import TASKS_FILENAME, TaskConfig
from agentstack import graph
from agentstack.generation import InsertionPoint

BASE_PATH = Path(__file__).parent


class FrameworksLanggraphTest(unittest.TestCase):
    def setUp(self):
        self.framework = os.getenv('TEST_FRAMEWORK')
        
        if not self.framework == frameworks.LANGGRAPH:
            self.skipTest("These tests are only for the LangGraph framework")
        
        self.project_dir = BASE_PATH / 'tmp' / self.framework / 'langgraph'
        conf.set_path(self.project_dir)
        os.makedirs(self.project_dir / 'src/config')

        shutil.copy(BASE_PATH / 'fixtures/agentstack.json', self.project_dir / 'agentstack.json')
        with conf.ConfigFile() as config:
            config.framework = frameworks.LANGGRAPH

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def test_get_import(self):
        """Test getting the import statement"""
        entrypoint_src = """
from agentstack import agent"""
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        import_ = entrypoint.get_import('agentstack', 'agent')
        assert isinstance(import_, ast.ImportFrom)

        missing = entrypoint.get_import('agentstack', 'task')
        assert missing is None

    def test_add_import(self):
        """Test adding an import statement"""
        entrypoint_src = """
from agentstack import agent"""
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        with LangGraphFile(self.project_dir / ENTRYPOINT) as entrypoint:
            entrypoint.add_import('agentstack', 'task')
        with open(self.project_dir / ENTRYPOINT, 'r') as f:
            new_src = f.read()

        assert 'from agentstack import task' in new_src
        assert 'from agentstack import agent' in new_src

    def test_missing_base_class(self):
        """A class with the name *Graph does not exist in the entrypoint"""
        entrypoint_src = """
class FooBar:
    pass
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_base_class()

    def test_missing_run_method(self):
        """A method named `run` does not exist in the base class"""
        entrypoint_src = """
class TestGraph:
    def foo(self):
        pass
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_run_method()

    def test_invalid_run_method(self):
        """The run method does not have the correct signature"""
        entrypoint_src = """
class TestGraph:
    def run(self, foo):
        pass
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_run_method()

    def test_global_tools_missing_toolnode(self):
        """A global tool is defined but the tool node is not present"""
        entrypoint_src = """
class TestGraph:
    def run(self, inputs: list):
        pass
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_global_tools()

    def test_global_tools_missing_list_in_toolnode(self):
        """A global tool is defined but the tool node does not have a list"""
        entrypoint_src = """
class TestGraph:
    def run(self, inputs: list):
        tools = ToolNode()
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_global_tools()

    def test_get_agent_tools_missing(self):
        """The agent method does not exist"""
        entrypoint_src = """
class TestGraph:
    def run(self, inputs: list):
        pass
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_agent_tools('test_agent')

    def test_get_agent_tools_missing_bind_tools(self):
        """An agent is defined but the bind_tools method is not present"""
        entrypoint_src = """
class TestGraph:
    @agentstack.agent
    def test_agent(self, state: State):
        pass
    def run(self, inputs: list):
        pass
    """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_agent_tools('test_agent')

    def test_get_agent_tools_bind_tools_invalid(self):
        """The bind_tools method call does not have the correct signature"""
        entrypoint_src = """
class TestGraph:
    @agentstack.agent
    def test_agent(self, state: State):
        agent = agent.bind_tools()
    def run(self, inputs: list):
        pass
    """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_agent_tools('test_agent')

    def _populate_graph_entrypoint(self):
        shutil.copy(BASE_PATH / "fixtures/agents_max.yaml", self.project_dir / AGENTS_FILENAME)
        shutil.copy(BASE_PATH / "fixtures/tasks_max.yaml", self.project_dir / TASKS_FILENAME)
        entrypoint_src = """
class TestGraph:
    @agentstack.agent
    def agent_name(self, state: State):
        pass
    @agentstack.task
    def task_name(self, state: State):
        pass
    def run(self, inputs: list):
        self.graph = Graph()
        self.graph.add_node("agent_name", self.agent_name)
        self.graph.add_node("task_name", self.task_name)
        self.graph.add_edge(START, "agent_name")
        self.graph.add_edge("agent_name", "task_name")
        self.graph.add_edge("task_name", END)
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

    def test_get_graph_nodes(self):
        """Test getting the graph nodes"""
        self._populate_graph_entrypoint()

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        nodes = entrypoint.get_graph_nodes()
        assert len(nodes) == 2
        for node in nodes:
            assert isinstance(node, ast.Call)

    def test_get_graph_edge_nodes(self):
        """Test getting the graph edge nodes"""
        self._populate_graph_entrypoint()

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        nodes = entrypoint.get_graph_edge_nodes()
        assert len(nodes) == 3
        for node in nodes:
            assert isinstance(node, ast.Call)

    def test_get_graph_edge_nodes_invalid(self):
        """Test getting the graph edge nodes with an invalid edge"""
        entrypoint_src = """
class TestGraph:
    def run(self, inputs: list):
        self.graph = Graph()
        self.graph.add_edge(START, "agent_name", "foo")
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_graph_edge_nodes()

    def test_get_graph(self):
        """Test getting the graph object"""
        self._populate_graph_entrypoint()

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        graph_nodes = entrypoint.get_graph()
        for node in graph_nodes:
            assert isinstance(node, graph.Edge)
            assert isinstance(node.source, graph.Node)
            assert isinstance(node.target, graph.Node)
            assert node.source.name in ['START', 'agent_name', 'task_name']
            assert node.target.name in ['agent_name', 'task_name', 'END']
            if node.source.name in [
                'agent_name',
            ]:
                assert node.source.type is graph.NodeType.AGENT
            if node.target.name in [
                'task_name',
            ]:
                assert node.target.type is graph.NodeType.TASK
            if node.source.name in ['START', 'END']:
                assert node.source.type is graph.NodeType.SPECIAL
            if node.target.name in ['START', 'END']:
                assert node.target.type is graph.NodeType.SPECIAL

    def test_add_graph_edge(self):
        """Test adding an edge to the graph"""
        self._populate_graph_entrypoint()

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        entrypoint.add_graph_edge(
            graph.Edge(
                # agent and task name must exist in the agents and tasks fixtures.
                source=graph.Node(name='second_agent_name', type=graph.NodeType.AGENT),
                target=graph.Node(name='task_name_two', type=graph.NodeType.TASK),
            )
        )
        graph_nodes = entrypoint.get_graph()
        assert len(graph_nodes) == 4
        for node in graph_nodes:
            assert isinstance(node, graph.Edge)
            assert isinstance(node.source, graph.Node)
            assert isinstance(node.target, graph.Node)
            assert node.source.name in ['START', 'agent_name', 'task_name', 'second_agent_name']
            assert node.target.name in ['END', 'agent_name', 'task_name', 'task_name_two']

    def test_remove_graph_edge(self):
        """Test removing an edge from the graph"""
        self._populate_graph_entrypoint()

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        entrypoint.remove_graph_edge(
            graph.Edge(
                # agent and task name must exist in the agents and tasks fixtures.
                source=graph.Node(name='agent_name', type=graph.NodeType.AGENT),
                target=graph.Node(name='task_name', type=graph.NodeType.TASK),
            )
        )
        graph_nodes = entrypoint.get_graph()
        assert len(graph_nodes) == 2  # START -> test_agent, test_task -> END

    def test_get_graph_edge_nodes(self):
        """Test getting the graph edge nodes"""
        self._populate_graph_entrypoint()

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        nodes = entrypoint.get_graph_edge_nodes()
        assert len(nodes) == 3
        for node in nodes:
            assert isinstance(node, ast.Call)

    def test_get_graph_edge_nodes_invalid(self):
        """Test getting the graph edge nodes with an invalid edge"""
        entrypoint_src = """
class TestGraph:
    def run(self, inputs: list):
        self.graph = Graph()
        self.graph.add_edge(START, "agent_name", "foo")
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_graph_edge_nodes()

    def test_get_graph(self):
        """Test getting the graph object"""
        self._populate_graph_entrypoint()

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        graph_nodes = entrypoint.get_graph()
        for node in graph_nodes:
            assert isinstance(node, graph.Edge)
            assert isinstance(node.source, graph.Node)
            assert isinstance(node.target, graph.Node)
            assert node.source.name in ['START', 'agent_name', 'task_name']
            assert node.target.name in ['agent_name', 'task_name', 'END']
            if node.source.name in [
                'agent_name',
            ]:
                assert node.source.type is graph.NodeType.AGENT
            if node.target.name in [
                'task_name',
            ]:
                assert node.target.type is graph.NodeType.TASK
            if node.source.name in ['START', 'END']:
                assert node.source.type is graph.NodeType.SPECIAL
            if node.target.name in ['START', 'END']:
                assert node.target.type is graph.NodeType.SPECIAL

    def test_get_graph_invalid_node_type(self):
        """Test getting the graph object with an unattainable node type"""
        entrypoint_src = """
class TestGraph:
    def run(self, inputs: list):
        self.graph.add_node("agent_name", self.agent_name)
        self.graph.add_node("task_name", self.task_name)
        self.graph.add_edge(START, "agent_name")
        self.graph.add_edge("agent_name_invalid", "task_name")
        self.graph.add_edge("task_name", END)
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_graph()

    def test_get_graph_invalid_node_content(self):
        """Test getting the graph object with an unattainable node content"""
        entrypoint_src = """
class TestGraph:
    def run(self, inputs: list):
        self.graph.add_edge(False, "agent_name")
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_graph()

    def test_add_graph_edge(self):
        """Test adding an edge to the graph"""
        self._populate_graph_entrypoint()

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        entrypoint.add_graph_edge(
            graph.Edge(
                source=graph.Node(name='START', type=graph.NodeType.SPECIAL),
                target=graph.Node(name='second_agent_name', type=graph.NodeType.AGENT),
            )
        )
        entrypoint.add_graph_edge(
            graph.Edge(
                # agent and task name must exist in the agents and tasks fixtures.
                source=graph.Node(name='second_agent_name', type=graph.NodeType.AGENT),
                target=graph.Node(name='task_name_two', type=graph.NodeType.TASK),
            )
        )
        entrypoint.add_graph_edge(
            graph.Edge(
                source=graph.Node(name='task_name_two', type=graph.NodeType.TASK),
                target=graph.Node(name='END', type=graph.NodeType.SPECIAL),
            )
        )
        graph_nodes = entrypoint.get_graph()
        assert len(graph_nodes) == 6
        for node in graph_nodes:
            assert isinstance(node, graph.Edge)
            assert isinstance(node.source, graph.Node)
            assert isinstance(node.target, graph.Node)
            assert node.source.name in [
                'START',
                'agent_name',
                'task_name',
                'second_agent_name',
                'task_name_two',
            ]
            assert node.target.name in [
                'agent_name',
                'task_name',
                'task_name_two',
                'second_agent_name',
                'END',
            ]

    def test_remove_graph_edge(self):
        """Test removing an edge from the graph"""
        self._populate_graph_entrypoint()

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        entrypoint.remove_graph_edge(
            graph.Edge(
                # agent and task name must exist in the agents and tasks fixtures.
                source=graph.Node(name='agent_name', type=graph.NodeType.AGENT),
                target=graph.Node(name='task_name', type=graph.NodeType.TASK),
            )
        )
        graph_nodes = entrypoint.get_graph()
        assert len(graph_nodes) == 2

    def test_remove_graph_edge_invalid_node_content(self):
        """Test removing an edge from the graph with an invalid node content"""
        entrypoint_src = """
class TestGraph:
    def run(self, inputs: list):
        self.graph = Graph()
        self.graph.add_edge(False, "agent_name")
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.remove_graph_edge(
                graph.Edge(
                    source=graph.Node(name='START', type=graph.NodeType.SPECIAL),
                    target=graph.Node(name='agent_name', type=graph.NodeType.AGENT),
                )
            )

    def test_remove_graph_edge_missing(self):
        """Test removing an edge from the graph with a missing edge"""
        self._populate_graph_entrypoint()

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.remove_graph_edge(
                graph.Edge(
                    source=graph.Node(name='agent_name_invalid', type=graph.NodeType.AGENT),
                    target=graph.Node(name='agent_name', type=graph.NodeType.AGENT),
                )
            )

    # TODO move this test to test_frameworks.py once insertion points are implemented
    # in other frameworks
    @parameterized.expand(
        [
            (None,),
            (InsertionPoint.END,),
            (InsertionPoint.BEGIN,),
        ]
    )
    def test_add_agent(self, position: InsertionPoint):
        """Test adding an Agent to the graph"""
        self._populate_graph_entrypoint()

        agent_config = AgentConfig('second_agent_name')
        frameworks.add_agent(agent_config, position)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        graph_ = entrypoint.get_graph()

        assert len(graph_) == 4
        source_nodes = [edge.source.name for edge in graph_]
        target_nodes = [edge.target.name for edge in graph_]
        if position in (None, InsertionPoint.END):
            assert source_nodes == ['START', 'agent_name', 'task_name', 'second_agent_name']
            assert target_nodes == [
                'agent_name',
                'task_name',
                'second_agent_name',
                'END',
            ]
        elif position == InsertionPoint.BEGIN:
            # TODO ordering is correct but not intuitive
            assert source_nodes == ['agent_name', 'task_name', 'START', 'second_agent_name']
            assert target_nodes == ['task_name', 'END', 'second_agent_name', 'agent_name']

    # TODO move this test to test_frameworks.py once insertion points are implemented
    # in other frameworks
    @parameterized.expand(
        [
            (None,),
            (InsertionPoint.END,),
            (InsertionPoint.BEGIN,),
        ]
    )
    def test_add_task(self, position: InsertionPoint):
        """Test adding a node to the graph"""
        self._populate_graph_entrypoint()

        task_config = TaskConfig('task_name_two')
        frameworks.add_task(task_config, position)

        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        graph_ = entrypoint.get_graph()

        assert len(graph_) == 4
        source_nodes = [edge.source.name for edge in graph_]
        target_nodes = [edge.target.name for edge in graph_]
        if position in (None, InsertionPoint.END):
            assert source_nodes == ['START', 'agent_name', 'task_name', 'task_name_two']
            assert target_nodes == [
                'agent_name',
                'task_name',
                'task_name_two',
                'END',
            ]
        elif position == InsertionPoint.BEGIN:
            # TODO ordering is correct but not intuitive
            assert source_nodes == ['agent_name', 'task_name', 'START', 'task_name_two']
            assert target_nodes == ['task_name', 'END', 'task_name_two', 'agent_name']

    def test_remove_graph_node(self):
        """Test removing a node from the graph"""
        self._populate_graph_entrypoint()

        agent_config = AgentConfig('agent_name')
        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        entrypoint.add_graph_node(agent_config)
        graph_nodes = entrypoint.get_graph_nodes()
        assert len(graph_nodes) == 3

        entrypoint.remove_graph_node(agent_config)
        graph_nodes = entrypoint.get_graph_nodes()
        assert len(graph_nodes) == 2

    def test_remove_graph_node_invalid(self):
        """Test removing a node from the graph with an invalid node"""
        entrypoint_src = """
class TestGraph:
    def run(self, inputs: list):
        self.graph.add_node(False, self.agent_name)
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        agent_config = AgentConfig('agent_name')
        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.remove_graph_node(agent_config)

    def test_remove_graph_node_missing(self):
        """Test removing a node from the graph with a missing node"""
        self._populate_graph_entrypoint()

        agent_config = AgentConfig('second_agent_name')
        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.remove_graph_node(agent_config)
