import os, sys
from pathlib import Path
import shutil
import unittest
from parameterized import parameterized_class

from agentstack.conf import ConfigFile, set_path
from agentstack.exceptions import ValidationError
from agentstack import frameworks
from agentstack._tools import ToolConfig

BASE_PATH = Path(__file__).parent


@parameterized_class([{"framework": framework} for framework in frameworks.SUPPORTED_FRAMEWORKS])
class TestFrameworks(unittest.TestCase):
    def setUp(self):
        self.project_dir = BASE_PATH / 'tmp' / self.framework / 'test_frameworks'

        os.makedirs(self.project_dir)
        os.chdir(self.project_dir)  # importing the crewai module requires us to be in a working directory
        os.makedirs(self.project_dir / 'src')
        os.makedirs(self.project_dir / 'src' / 'tools')

        (self.project_dir / 'src' / '__init__.py').touch()
        (self.project_dir / 'src' / 'tools' / '__init__.py').touch()

        shutil.copy(BASE_PATH / 'fixtures' / 'agentstack.json', self.project_dir / 'agentstack.json')
        set_path(self.project_dir)
        with ConfigFile() as config:
            config.framework = self.framework

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def _populate_min_entrypoint(self):
        """This entrypoint does not have any tools or agents."""
        entrypoint_path = frameworks.get_entrypoint_path(self.framework)
        shutil.copy(BASE_PATH / f"fixtures/frameworks/{self.framework}/entrypoint_min.py", entrypoint_path)

    def _populate_max_entrypoint(self):
        """This entrypoint has tools and agents."""
        entrypoint_path = frameworks.get_entrypoint_path(self.framework)
        shutil.copy(BASE_PATH / f"fixtures/frameworks/{self.framework}/entrypoint_max.py", entrypoint_path)

    def _get_test_tool(self) -> ToolConfig:
        return ToolConfig(name='test_tool', category='test', tools=['test_tool'])

    def _get_test_tool_alternate(self) -> ToolConfig:
        return ToolConfig(name='test_tool_alt', category='test', tools=['test_tool_alt'])

    def test_get_framework_module(self):
        module = frameworks.get_framework_module(self.framework)
        assert module.__name__ == f"agentstack.frameworks.{self.framework}"

    def test_get_framework_module_invalid(self):
        with self.assertRaises(Exception) as context:
            frameworks.get_framework_module('invalid')

    def test_validate_project(self):
        self._populate_max_entrypoint()
        frameworks.validate_project()

    def test_validate_project_invalid(self):
        self._populate_min_entrypoint()
        with self.assertRaises(ValidationError) as context:
            frameworks.validate_project()

    def test_add_tool(self):
        self._populate_max_entrypoint()
        frameworks.add_tool(self._get_test_tool(), 'test_agent')

        entrypoint_src = open(frameworks.get_entrypoint_path(self.framework)).read()
        assert "*agentstack.tools['test_tool']" in entrypoint_src

    def test_add_tool_invalid(self):
        self._populate_min_entrypoint()
        with self.assertRaises(ValidationError) as context:
            frameworks.add_tool(self._get_test_tool(), 'test_agent')

    def test_remove_tool(self):
        self._populate_max_entrypoint()
        frameworks.add_tool(self._get_test_tool(), 'test_agent')
        frameworks.remove_tool(self._get_test_tool(), 'test_agent')

        entrypoint_src = open(frameworks.get_entrypoint_path(self.framework)).read()
        assert "*agentstack.tools['test_tool']" not in entrypoint_src

    def test_add_multiple_tools(self):
        self._populate_max_entrypoint()
        frameworks.add_tool(self._get_test_tool(), 'test_agent')
        frameworks.add_tool(self._get_test_tool_alternate(), 'test_agent')

        entrypoint_src = open(frameworks.get_entrypoint_path(self.framework)).read()
        assert (  # ordering is not guaranteed
            "*agentstack.tools['test_tool'], *agentstack.tools['test_tool_alt']" in entrypoint_src
            or "*agentstack.tools['test_tool_alt'], *agentstack.tools['test_tool']" in entrypoint_src
        )

    def test_remove_one_tool_of_multiple(self):
        self._populate_max_entrypoint()
        frameworks.add_tool(self._get_test_tool(), 'test_agent')
        frameworks.add_tool(self._get_test_tool_alternate(), 'test_agent')
        frameworks.remove_tool(self._get_test_tool(), 'test_agent')

        entrypoint_src = open(frameworks.get_entrypoint_path(self.framework)).read()
        assert "*agentstack.tools['test_tool']" not in entrypoint_src
        assert "*agentstack.tools['test_tool_alt']" in entrypoint_src
