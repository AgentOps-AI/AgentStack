import subprocess
import os, sys
import unittest
from parameterized import parameterized
from pathlib import Path
import shutil
from agentstack._tools import get_all_tool_names
from cli_test_utils import run_cli
from agentstack.utils import validator_not_empty
from agentstack.cli import get_validated_input
from unittest.mock import patch
from inquirer.errors import ValidationError


BASE_PATH = Path(__file__).parent
TEMPLATE_NAME = "empty"

class CLIToolsTest(unittest.TestCase):
    def setUp(self):
        self.framework = os.getenv('TEST_FRAMEWORK')
        self.project_dir = BASE_PATH / 'tmp' / self.framework / 'cli_tools'
        os.makedirs(self.project_dir, exist_ok=True)
        os.chdir(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.project_dir, ignore_errors=True)

    @parameterized.expand([(x,) for x in get_all_tool_names()])
    @unittest.skip("Dependency resolution issue")
    def test_add_tool(self, tool_name):
        """Test the adding every tool to a project."""
        result = run_cli('init', f"{tool_name}_project", "--template", TEMPLATE_NAME)
        self.assertEqual(result.returncode, 0)
        os.chdir(self.project_dir / f"{tool_name}_project")
        result = run_cli('generate', 'agent', 'test_agent', '--llm', 'opeenai/gpt-4o')
        self.assertEqual(result.returncode, 0)
        result = run_cli('generate', 'task', 'test_task')
        self.assertEqual(result.returncode, 0)

        result = run_cli('tools', 'add', tool_name)
        print(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.project_dir.exists())

    def test_get_validated_input(self):
        """Test the get_validated_input function with various validation scenarios"""

        # Test basic input
        with patch('inquirer.text', return_value='test_input'):
            result = get_validated_input("Test message")
            self.assertEqual(result, 'test_input')

        # Test min length validation - valid input
        with patch('inquirer.text', return_value='abc'):
            result = get_validated_input("Test message", min_length=3)
            self.assertEqual(result, 'abc')

        # Test min length validation - invalid input should raise ValidationError
        validator = validator_not_empty(3)
        with self.assertRaises(ValidationError):
            validator(None, 'ab')

        # Test snake_case validation
        with patch('inquirer.text', return_value='test_case'):
            result = get_validated_input("Test message", snake_case=True)
            self.assertEqual(result, 'test_case')

    def test_create_tool_basic(self):
        """Test creating a new custom tool via CLI"""
        # Initialize a project first
        result = run_cli('init', "test_project", "--template", TEMPLATE_NAME)
        self.assertEqual(result.returncode, 0)
        os.chdir(self.project_dir / "test_project")

        # Create an agent to test with
        result = run_cli('generate', 'agent', 'test_agent', '--llm', 'openai/gpt-4')
        self.assertEqual(result.returncode, 0)

        # Create a new tool
        result = run_cli('tools', 'new', 'test_tool')
        self.assertEqual(result.returncode, 0)

        # Verify tool directory and files were created
        tool_path = self.project_dir / "test_project" / 'src/tools/test_tool'
        self.assertTrue(tool_path.exists())
        self.assertTrue((tool_path / '__init__.py').exists())
        self.assertTrue((tool_path / 'config.json').exists())

    def test_create_tool_with_agents(self):
        """Test creating a new custom tool with specific agents via CLI"""
        # Initialize project and create multiple agents
        result = run_cli('init', "test_project", "--template", TEMPLATE_NAME)
        self.assertEqual(result.returncode, 0)
        os.chdir(self.project_dir / "test_project")

        run_cli('generate', 'agent', 'agent1', '--llm', 'openai/gpt-4')
        run_cli('generate', 'agent', 'agent2', '--llm', 'openai/gpt-4')

        # Create tool with specific agent
        result = run_cli('tools', 'new', 'test_tool', '--agents', 'agent1')
        self.assertEqual(result.returncode, 0)

        # Verify tool was created
        tool_path = self.project_dir / "test_project" / 'src/tools/test_tool'
        self.assertTrue(tool_path.exists())

    def test_create_tool_existing(self):
        """Test creating a tool that already exists"""
        # Initialize project
        result = run_cli('init', "test_project", "--template", TEMPLATE_NAME)
        self.assertEqual(result.returncode, 0)
        os.chdir(self.project_dir / "test_project")

        # Create agent
        run_cli('generate', 'agent', 'test_agent', '--llm', 'openai/gpt-4')

        # Create tool first time
        result = run_cli('tools', 'new', 'test_tool')
        self.assertEqual(result.returncode, 0)

        # Try to create same tool again
        result = run_cli('tools', 'new', 'test_tool')
        self.assertNotEqual(result.returncode, 0)  # Should fail
        self.assertIn("already exists", result.stderr)

    def test_create_tool_invalid_name(self):
        """Test creating a tool with invalid name formats"""
        # Initialize project
        result = run_cli('init', "test_project", "--template", TEMPLATE_NAME)
        self.assertEqual(result.returncode, 0)
        os.chdir(self.project_dir / "test_project")

        # Create agent
        run_cli('generate', 'agent', 'test_agent', '--llm', 'openai/gpt-4')

        # Test various invalid names
        invalid_names = ['TestTool', 'test-tool', 'test tool']
        for name in invalid_names:
            result = run_cli('tools', 'new', name)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must be snake_case", result.stderr)

    def test_create_tool_no_project(self):
        """Test creating a tool outside a project directory"""
        # Try to create tool without initializing project
        result = run_cli('tools', 'new', 'test_tool')
        self.assertNotEqual(result.returncode, 0)