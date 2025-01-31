import os, sys
import shutil
import unittest
from pathlib import Path
import ast
from agentstack import conf
from agentstack.exceptions import ValidationError
from agentstack import frameworks
from agentstack.frameworks.openai_swarm import ENTRYPOINT, SwarmFile
from agentstack.agents import AGENTS_FILENAME, AgentConfig
from agentstack.tasks import TASKS_FILENAME, TaskConfig

BASE_PATH = Path(__file__).parent


class FrameworksOpenAISwarmTest(unittest.TestCase):
    def setUp(self):
        self.framework = os.getenv('TEST_FRAMEWORK')
        
        if not self.framework == frameworks.OPENAI_SWARM:
            self.skipTest("These tests are only for the OpenAI Swarm framework")
        
        self.project_dir = BASE_PATH / 'tmp' / self.framework / 'openai_swarm'
        conf.set_path(self.project_dir)
        os.makedirs(self.project_dir / 'src/config')

        shutil.copy(BASE_PATH / 'fixtures/agentstack.json', self.project_dir / 'agentstack.json')
        with conf.ConfigFile() as config:
            config.framework = frameworks.OPENAI_SWARM

    def tearDown(self):
        shutil.rmtree(self.project_dir)
    
    def test_missing_base_class(self):
        """A class with the name *Stack does not exist in the entrypoint"""
        entrypoint_src = """
class FooBar:
    pass
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = SwarmFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_base_class()

    def test_missing_run_method(self):
        """A method named `run` does not exist in the base class"""
        entrypoint_src = """
class TestStack:
    def foo(self):
        pass
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = SwarmFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_run_method()

    def test_invalid_run_method(self):
        """The run method does not have the correct signature"""
        entrypoint_src = """
class TestStack:
    def run(self, foo):
        pass
        """
        with open(self.project_dir / ENTRYPOINT, 'w') as f:
            f.write(entrypoint_src)

        entrypoint = SwarmFile(self.project_dir / ENTRYPOINT)
        with self.assertRaises(ValidationError):
            entrypoint.get_run_method()

