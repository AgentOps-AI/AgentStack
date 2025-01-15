import os, sys
import shutil
import unittest
import parameterized
from pathlib import Path
from agentstack import conf
from agentstack.exceptions import ValidationError
from agentstack.frameworks.langgraph import ENTRYPOINT, LangGraphFile

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

