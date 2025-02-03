import os, sys
from pathlib import Path
import shutil
import unittest
from parameterized import parameterized_class
import ast

from agentstack.conf import ConfigFile, set_path
from agentstack import frameworks
from agentstack._tools import get_all_tools, ToolConfig
from agentstack.generation.tool_generation import add_tool, remove_tool


BASE_PATH = Path(__file__).parent


# TODO parameterize all tools
class TestGenerationTool(unittest.TestCase):
    def setUp(self):
        self.framework = os.getenv('TEST_FRAMEWORK')
        self.project_dir = BASE_PATH / 'tmp' / self.framework / 'tool_generation'

        os.makedirs(self.project_dir)
        os.makedirs(self.project_dir / 'src')
        os.makedirs(self.project_dir / 'src' / 'tools')
        (self.project_dir / 'src' / '__init__.py').touch()

        # set the framework in agentstack.json
        shutil.copy(BASE_PATH / 'fixtures' / 'agentstack.json', self.project_dir / 'agentstack.json')
        set_path(self.project_dir)
        with ConfigFile() as config:
            config.framework = self.framework

        # populate the entrypoint
        entrypoint_path = frameworks.get_entrypoint_path(self.framework)
        shutil.copy(BASE_PATH / f"fixtures/frameworks/{self.framework}/entrypoint_max.py", entrypoint_path)

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def test_add_tool(self):
        tool_conf = ToolConfig.from_tool_name('agent_connect')
        add_tool('agent_connect')

        entrypoint_path = frameworks.get_entrypoint_path(self.framework)
        entrypoint_src = open(entrypoint_path).read()
        ast.parse(entrypoint_src)  # validate syntax

        # TODO verify tool is added to all agents (this is covered in test_frameworks.py)
        # assert 'agent_connect' in entrypoint_src
        assert 'agent_connect' in open(self.project_dir / 'agentstack.json').read()

    def test_remove_tool(self):
        tool_conf = ToolConfig.from_tool_name('agent_connect')
        add_tool('agent_connect')
        remove_tool('agent_connect')

        entrypoint_path = frameworks.get_entrypoint_path(self.framework)
        entrypoint_src = open(entrypoint_path).read()
        ast.parse(entrypoint_src)  # validate syntax

        # TODO verify tool is removed from all agents (this is covered in test_frameworks.py)
        # assert 'agent_connect' not in entrypoint_src
        assert 'agent_connect' not in open(self.project_dir / 'agentstack.json').read()
