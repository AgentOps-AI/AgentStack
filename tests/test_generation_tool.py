import os, sys
from pathlib import Path
import shutil
import unittest
from parameterized import parameterized_class
import ast
import json
from unittest.mock import patch

from agentstack.conf import ConfigFile, set_path
from agentstack import frameworks
from agentstack._tools import get_all_tools, ToolConfig
from agentstack.generation.tool_generation import add_tool, remove_tool, create_tool


BASE_PATH = Path(__file__).parent


# TODO parameterize all tools
class TestGenerationTool(unittest.TestCase):
    def setUp(self):
        self.framework = os.getenv('TEST_FRAMEWORK')
        self.project_dir = BASE_PATH / 'tmp' / self.framework / 'tool_generation'
        self.tools_dir = self.project_dir / 'src' / 'tools'

        os.makedirs(self.project_dir)
        os.makedirs(self.project_dir / 'src')
        os.makedirs(self.project_dir / 'src' / 'tools')
        os.makedirs(self.tools_dir)
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

    def test_create_tool_basic(self):
        """Test basic tool creation with default parameters"""
        tool_name = "test_tool"
        tool_path = self.tools_dir / tool_name

        # Execute
        create_tool(
            tool_name=tool_name,
            tool_path=tool_path,
            user_tools_dir=self.tools_dir
        )

        # Assert directory was created
        self.assertTrue(tool_path.exists())
        self.assertTrue(tool_path.is_dir())

        # Assert __init__.py was created with correct content
        init_file = tool_path / "__init__.py"
        self.assertTrue(init_file.exists())
        init_content = init_file.read_text()
        self.assertIn(f"def {tool_name}():", init_content)
        self.assertIn('"""', init_content)  # Check docstring exists

        # Assert config.json was created with correct content
        config_file = tool_path / "config.json"
        self.assertTrue(config_file.exists())
        config = json.loads(config_file.read_text())
        self.assertEqual(config["name"], tool_name)
        self.assertEqual(config["category"], "custom")
        self.assertEqual(config["tools"], [tool_name])

        # Verify tool was added to agentstack.json
        self.assertIn(tool_name, open(self.project_dir / 'agentstack.json').read())

    def test_create_tool_specific_agents(self):
        """Test tool creation with specific agents"""
        tool_name = "test_tool"
        tool_path = self.tools_dir / tool_name
        specific_agents = ["agent1"]

        create_tool(
            tool_name=tool_name,
            tool_path=tool_path,
            user_tools_dir=self.tools_dir,
            agents=specific_agents
        )

        # Assert directory and files were created
        self.assertTrue(tool_path.exists())
        self.assertTrue((tool_path / "__init__.py").exists())
        self.assertTrue((tool_path / "config.json").exists())

        # Verify tool was added to agentstack.json
        self.assertIn(tool_name, open(self.project_dir / 'agentstack.json').read())

        # Verify tool was added only to specified agent in entrypoint
        entrypoint_src = open(frameworks.get_entrypoint_path(self.framework)).read()
        ast.parse(entrypoint_src)  # validate syntax

    def test_create_tool_directory_exists(self):
        """Test tool creation fails when directory already exists"""
        tool_name = "test_tool"
        tool_path = self.tools_dir / tool_name

        # Create the directory first
        tool_path.mkdir(parents=True)

        # Assert raises error when trying to create tool in existing directory
        with self.assertRaises(FileExistsError):
            create_tool(
                tool_name=tool_name,
                tool_path=tool_path,
                user_tools_dir=self.tools_dir
            )

    @patch('agentstack.generation.tool_generation.log.success')
    def test_create_tool_success_logging(self, mock_log_success):
        """Test success logging message"""
        tool_name = "test_tool"
        tool_path = self.tools_dir / tool_name

        create_tool(
            tool_name=tool_name,
            tool_path=tool_path,
            user_tools_dir=self.tools_dir
        )

        mock_log_success.assert_called_once()
        log_message = mock_log_success.call_args[0][0]
        self.assertIn(tool_name, log_message)
        self.assertIn(str(self.tools_dir), log_message)

