import os, sys
import shutil
import unittest
import parameterized
from pathlib import Path
import ast
from agentstack import conf
from agentstack.exceptions import ValidationError
from agentstack.frameworks.langgraph import ENTRYPOINT, LangGraphFile
from agentstack.agents import AGENTS_FILENAME, AgentConfig
from agentstack.tasks import TASKS_FILENAME, TaskConfig
from agentstack import graph

BASE_PATH = Path(__file__).parent


class FrameworksLanggraphTest(unittest.TestCase):
    def setUp(self):
        self.project_dir = BASE_PATH / 'tmp/frameworks/langgraph'
        conf.set_path(self.project_dir)
        os.makedirs(self.project_dir / 'src/config')

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    @parameterized.parameterized.expand([
        ('openai', "ChatOpenAI"), 
        ('anthropic', "ChatAnthropic"),
    ])
    def test_get_agent_provider_class_name(self, provider, class_name):
        """Test getting the agent provider class name"""
        (self.project_dir / ENTRYPOINT).touch()
        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        assert entrypoint.get_agent_provider_class_name(provider) == class_name

    def test_get_agent_provider_class_name_invalid(self):
        """Test getting the agent provider class name with an invalid provider"""
        (self.project_dir / ENTRYPOINT).touch()
        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_agent_provider_class_name('invalid')

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
        entrypoint_src = """
class TestGraph:
    @agentstack.agent
    def test_agent(self, state: State):
        pass
    @agentstack.task
    def test_task(self, state: State):
        pass
    def run(self, inputs: list):
        self.graph = Graph()
        self.graph.add_node("test_agent", self.test_agent)
        self.graph.add_node("test_task", self.test_task)
        self.graph.add_edge("test_agent", "test_task")
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
        assert len(nodes) == 1
        for node in nodes:
            assert isinstance(node, ast.Call)
    
    def test_get_graph(self):
        """Test getting the graph object"""
        self._populate_graph_entrypoint()
        
        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        graph_nodes = entrypoint.get_graph()
        for node in graph_nodes:
            assert isinstance(node, graph.Edge)
            assert isinstance(node.source, graph.Node)
            assert isinstance(node.target, graph.Node)
            assert node.source.name in ['test_agent']
            assert node.target.name in ['test_task']
    
    def test_add_graph_edge(self):
        """Test adding an edge to the graph"""
        self._populate_graph_entrypoint()
        
        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        entrypoint.add_graph_edge(graph.Edge(
            source=graph.Node(name='test_agent2'),
            target=graph.Node(name='test_task2')
        ))
        graph_nodes = entrypoint.get_graph()
        assert len(graph_nodes) == 2
        for node in graph_nodes:
            assert isinstance(node, graph.Edge)
            assert isinstance(node.source, graph.Node)
            assert isinstance(node.target, graph.Node)
            assert node.source.name in ['test_agent', 'test_agent2']
            assert node.target.name in ['test_task', 'test_task2']
    
    def test_remove_graph_edge(self):
        """Test removing an edge from the graph"""
        self._populate_graph_entrypoint()
        
        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        entrypoint.remove_graph_edge(graph.Edge(
            source=graph.Node(name='test_agent'),
            target=graph.Node(name='test_task')
        ))
        graph_nodes = entrypoint.get_graph()
        assert len(graph_nodes) == 0
    
    def test_add_graph_node_agent(self):
        """Test adding a node to the graph"""
        self._populate_graph_entrypoint()
        shutil.copy(BASE_PATH / "fixtures/agents_max.yaml", self.project_dir / AGENTS_FILENAME)
        
        agent_config = AgentConfig('agent_name')
        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        entrypoint.add_graph_node(agent_config)
        graph_nodes = entrypoint.get_graph_nodes()
        assert len(graph_nodes) == 3
        for node in graph_nodes:
            assert isinstance(node, ast.Call)
            assert node.func.attr == 'add_node'
            assert node.args[0].s in ['test_agent', 'test_task', 'agent_name']
    
    def test_add_graph_node_task(self):
        """Test adding a node to the graph"""
        self._populate_graph_entrypoint()
        shutil.copy(BASE_PATH / "fixtures/tasks_max.yaml", self.project_dir / TASKS_FILENAME)
        
        task_config = TaskConfig('task_name')
        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        entrypoint.add_graph_node(task_config)
        graph_nodes = entrypoint.get_graph_nodes()
        assert len(graph_nodes) == 3
        for node in graph_nodes:
            assert isinstance(node, ast.Call)
            assert node.func.attr == 'add_node'
            assert node.args[0].s in ['test_agent', 'test_task', 'task_name']
    
    def test_remove_graph_node(self):
        """Test removing a node from the graph"""
        self._populate_graph_entrypoint()
        shutil.copy(BASE_PATH / "fixtures/agents_max.yaml", self.project_dir / AGENTS_FILENAME)
        
        agent_config = AgentConfig('agent_name')
        entrypoint = LangGraphFile(self.project_dir / ENTRYPOINT)
        entrypoint.add_graph_node(agent_config)
        graph_nodes = entrypoint.get_graph_nodes()
        assert len(graph_nodes) == 3
        
        entrypoint.remove_graph_node(agent_config)
        graph_nodes = entrypoint.get_graph_nodes()
        assert len(graph_nodes) == 2