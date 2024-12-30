import os, sys
from pathlib import Path
import shutil
import unittest
from parameterized import parameterized_class

from agentstack import conf
from agentstack.conf import ConfigFile
from agentstack.exceptions import ValidationError
from agentstack import frameworks
from agentstack.tools import ToolConfig
from agentstack.generation.tool_generation import ToolsInitFile, TOOLS_INIT_FILENAME


BASE_PATH = Path(__file__).parent


@parameterized_class([{"framework": framework} for framework in frameworks.SUPPORTED_FRAMEWORKS])
class TestToolGenerationInit(unittest.TestCase):
    def setUp(self):
        self.project_dir = BASE_PATH / 'tmp' / 'tool_generation_init'
        os.makedirs(self.project_dir)
        os.makedirs(self.project_dir / 'src')
        os.makedirs(self.project_dir / 'src' / 'tools')
        (self.project_dir / 'src' / '__init__.py').touch()
        (self.project_dir / 'src' / 'tools' / '__init__.py').touch()
        shutil.copy(BASE_PATH / 'fixtures' / 'agentstack.json', self.project_dir / 'agentstack.json')

        conf.set_path(self.project_dir)
        with ConfigFile() as config:
            config.framework = self.framework

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def _get_test_tool(self) -> ToolConfig:
        return ToolConfig(name='test_tool', category='test', tools=['test_tool'])

    def _get_test_tool_alt(self) -> ToolConfig:
        return ToolConfig(name='test_tool_alt', category='test', tools=['test_tool_alt'])

    def test_tools_init_file(self):
        tools_init = ToolsInitFile(conf.PATH / TOOLS_INIT_FILENAME)
        # file is empty
        assert tools_init.get_import_for_tool(self._get_test_tool()) == None

    def test_tools_init_file_missing(self):
        with self.assertRaises(ValidationError) as context:
            tools_init = ToolsInitFile(conf.PATH / 'missing')

    def test_tools_init_file_add_import(self):
        tool = self._get_test_tool()
        with ToolsInitFile(conf.PATH / TOOLS_INIT_FILENAME) as tools_init:
            tools_init.add_import_for_tool(tool, self.framework)

        tool_init_src = open(self.project_dir / TOOLS_INIT_FILENAME).read()
        assert tool.get_import_statement(self.framework) in tool_init_src

    def test_tools_init_file_add_import_multiple(self):
        tool = self._get_test_tool()
        tool_alt = self._get_test_tool_alt()
        with ToolsInitFile(conf.PATH / TOOLS_INIT_FILENAME) as tools_init:
            tools_init.add_import_for_tool(tool, self.framework)

        with ToolsInitFile(conf.PATH / TOOLS_INIT_FILENAME) as tools_init:
            tools_init.add_import_for_tool(tool_alt, self.framework)

        # Should not be able to re-add a tool import
        with self.assertRaises(ValidationError) as context:
            with ToolsInitFile(conf.PATH / TOOLS_INIT_FILENAME) as tools_init:
                tools_init.add_import_for_tool(tool, self.framework)

        tool_init_src = open(self.project_dir / TOOLS_INIT_FILENAME).read()
        assert tool.get_import_statement(self.framework) in tool_init_src
        assert tool_alt.get_import_statement(self.framework) in tool_init_src
        # TODO this might be a little too strict
        assert (
            tool_init_src
            == """
from .test_tool_tool import test_tool
from .test_tool_alt_tool import test_tool_alt"""
        )
