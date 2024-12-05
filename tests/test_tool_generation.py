import os, sys
from pathlib import Path
import shutil
import unittest
from parameterized import parameterized_class

from agentstack import frameworks
from agentstack.tools import get_all_tools, ToolConfig
from agentstack.generation.files import ConfigFile
from agentstack.generation.tool_generation import add_tool, remove_tool, TOOLS_INIT_FILENAME


BASE_PATH = Path(__file__).parent

# TODO parameterize all tools
@parameterized_class([
    {"framework": framework} for framework in frameworks.SUPPORTED_FRAMEWORKS
])
class TestToolGeneration(unittest.TestCase):
    def setUp(self):
        self.project_dir = BASE_PATH/'tmp'/'tool_generation'
        
        os.makedirs(self.project_dir)
        os.makedirs(self.project_dir/'src')
        os.makedirs(self.project_dir/'src'/'tools')
        (self.project_dir/'src'/'__init__.py').touch()
        (self.project_dir/TOOLS_INIT_FILENAME).touch()
        
        # populate the entrypoint
        entrypoint_path = frameworks.get_entrypoint_path(self.framework, self.project_dir)
        shutil.copy(BASE_PATH/f"fixtures/frameworks/{self.framework}/entrypoint_max.py", entrypoint_path)
        
        # set the framework in agentstack.json
        shutil.copy(BASE_PATH/'fixtures'/'agentstack.json', self.project_dir/'agentstack.json')
        with ConfigFile(self.project_dir) as config:
            config.framework = self.framework
    
    def tearDown(self):
        shutil.rmtree(self.project_dir)
    
    def test_add_tool(self):
        tool_conf = ToolConfig.from_tool_name('agent_connect')
        add_tool('agent_connect', path=self.project_dir)
        
        entrypoint_path = frameworks.get_entrypoint_path(self.framework, self.project_dir)
        entrypoint_src = open(entrypoint_path).read()
        tools_init_src = open(self.project_dir/TOOLS_INIT_FILENAME).read()
        
        # TODO verify tool is added to all agents (this is covered in test_frameworks.py)
        #assert 'agent_connect' in entrypoint_src
        assert f'from .{tool_conf.module_name} import' in tools_init_src
        assert (self.project_dir/'src'/'tools'/f'{tool_conf.module_name}.py').exists()
        assert 'agent_connect' in open(self.project_dir/'agentstack.json').read()
    
    def test_remove_tool(self):
        tool_conf = ToolConfig.from_tool_name('agent_connect')
        add_tool('agent_connect', path=self.project_dir)
        remove_tool('agent_connect', path=self.project_dir)
        
        entrypoint_path = frameworks.get_entrypoint_path(self.framework, self.project_dir)
        entrypoint_src = open(entrypoint_path).read()
        tools_init_src = open(self.project_dir/TOOLS_INIT_FILENAME).read()
        
        # TODO verify tool is removed from all agents (this is covered in test_frameworks.py)
        #assert 'agent_connect' not in entrypoint_src
        assert f'from .{tool_conf.module_name} import' not in tools_init_src
        assert not (self.project_dir/'src'/'tools'/f'{tool_conf.module_name}.py').exists()
        assert 'agent_connect' not in open(self.project_dir/'agentstack.json').read()

