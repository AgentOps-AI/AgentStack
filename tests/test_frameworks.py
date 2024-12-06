import os, sys
from pathlib import Path
import shutil
import unittest
from parameterized import parameterized_class

from agentstack import ValidationError
from agentstack import frameworks
from agentstack.tools import ToolConfig

BASE_PATH = Path(__file__).parent


@parameterized_class([{"framework": framework} for framework in frameworks.SUPPORTED_FRAMEWORKS])
class TestFrameworks(unittest.TestCase):
    def setUp(self):
        self.project_dir = BASE_PATH / 'tmp' / self.framework

        os.makedirs(self.project_dir)
        os.makedirs(self.project_dir / 'src')
        os.makedirs(self.project_dir / 'src' / 'tools')

        (self.project_dir / 'src' / '__init__.py').touch()
        (self.project_dir / 'src' / 'tools' / '__init__.py').touch()

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def _populate_min_entrypoint(self):
        """This entrypoint does not have any tools or agents."""
        entrypoint_path = frameworks.get_entrypoint_path(self.framework, self.project_dir)
        shutil.copy(BASE_PATH / f"fixtures/frameworks/{self.framework}/entrypoint_min.py", entrypoint_path)

    def _populate_max_entrypoint(self):
        """This entrypoint has tools and agents."""
        entrypoint_path = frameworks.get_entrypoint_path(self.framework, self.project_dir)
        shutil.copy(BASE_PATH / f"fixtures/frameworks/{self.framework}/entrypoint_max.py", entrypoint_path)

    def _get_test_tool(self) -> ToolConfig:
        return ToolConfig(name='test_tool', category='test', tools=['test_tool'])

    def _get_test_tool_starred(self) -> ToolConfig:
        return ToolConfig(
            name='test_tool_star', category='test', tools=['test_tool_star'], tools_bundled=True
        )

    def test_get_framework_module(self):
        module = frameworks.get_framework_module(self.framework)
        assert module.__name__ == f"agentstack.frameworks.{self.framework}"

    def test_get_framework_module_invalid(self):
        with self.assertRaises(Exception) as context:
            frameworks.get_framework_module('invalid')

    def test_validate_project(self):
        self._populate_max_entrypoint()
        frameworks.validate_project(self.framework, self.project_dir)

    def test_validate_project_invalid(self):
        self._populate_min_entrypoint()
        with self.assertRaises(ValidationError) as context:
            frameworks.validate_project(self.framework, self.project_dir)

    def test_add_tool(self):
        self._populate_max_entrypoint()
        frameworks.add_tool(self.framework, self._get_test_tool(), 'test_agent', self.project_dir)

        entrypoint_src = open(frameworks.get_entrypoint_path(self.framework, self.project_dir)).read()
        # TODO these asserts are not framework agnostic
        assert 'tools=[tools.test_tool' in entrypoint_src

    def test_add_tool_starred(self):
        self._populate_max_entrypoint()
        frameworks.add_tool(self.framework, self._get_test_tool_starred(), 'test_agent', self.project_dir)

        entrypoint_src = open(frameworks.get_entrypoint_path(self.framework, self.project_dir)).read()
        assert 'tools=[*tools.test_tool_star' in entrypoint_src

    def test_add_tool_invalid(self):
        self._populate_min_entrypoint()
        with self.assertRaises(ValidationError) as context:
            frameworks.add_tool(self.framework, self._get_test_tool(), 'test_agent', self.project_dir)

    def test_remove_tool(self):
        self._populate_max_entrypoint()
        frameworks.add_tool(self.framework, self._get_test_tool(), 'test_agent', self.project_dir)
        frameworks.remove_tool(self.framework, self._get_test_tool(), 'test_agent', self.project_dir)

        entrypoint_src = open(frameworks.get_entrypoint_path(self.framework, self.project_dir)).read()
        assert 'tools=[tools.test_tool' not in entrypoint_src

    def test_remove_tool_starred(self):
        self._populate_max_entrypoint()
        frameworks.add_tool(self.framework, self._get_test_tool_starred(), 'test_agent', self.project_dir)
        frameworks.remove_tool(self.framework, self._get_test_tool_starred(), 'test_agent', self.project_dir)

        entrypoint_src = open(frameworks.get_entrypoint_path(self.framework, self.project_dir)).read()
        assert 'tools=[*tools.test_tool_star' not in entrypoint_src

    def test_add_multiple_tools(self):
        self._populate_max_entrypoint()
        frameworks.add_tool(self.framework, self._get_test_tool(), 'test_agent', self.project_dir)
        frameworks.add_tool(self.framework, self._get_test_tool_starred(), 'test_agent', self.project_dir)

        entrypoint_src = open(frameworks.get_entrypoint_path(self.framework, self.project_dir)).read()
        assert (  # ordering is not guaranteed
            'tools=[tools.test_tool, *tools.test_tool_star' in entrypoint_src
            or 'tools=[*tools.test_tool_star, tools.test_tool' in entrypoint_src
        )

    def test_remove_one_tool_of_multiple(self):
        self._populate_max_entrypoint()
        frameworks.add_tool(self.framework, self._get_test_tool(), 'test_agent', self.project_dir)
        frameworks.add_tool(self.framework, self._get_test_tool_starred(), 'test_agent', self.project_dir)
        frameworks.remove_tool(self.framework, self._get_test_tool(), 'test_agent', self.project_dir)

        entrypoint_src = open(frameworks.get_entrypoint_path(self.framework, self.project_dir)).read()
        assert 'tools=[tools.test_tool' not in entrypoint_src
        assert 'tools=[*tools.test_tool_star' in entrypoint_src
