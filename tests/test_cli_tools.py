import subprocess
import os, sys
import unittest
from parameterized import parameterized
from pathlib import Path
import shutil
from agentstack.tools import get_all_tool_names
from cli_test_utils import run_cli
from agentstack.utils import validator_not_empty
from agentstack.cli.cli import get_validated_input
from unittest.mock import patch
from inquirer.errors import ValidationError
from agentstack.utils import validator_not_empty


BASE_PATH = Path(__file__).parent

# TODO parameterized framework
class CLIToolsTest(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path(BASE_PATH / 'tmp/cli_tools')
        os.makedirs(self.project_dir, exist_ok=True)
        os.chdir(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.project_dir, ignore_errors=True)

    @parameterized.expand([(x,) for x in get_all_tool_names()])
    @unittest.skip("Dependency resolution issue")
    def test_add_tool(self, tool_name):
        """Test the adding every tool to a project."""
        result = run_cli('init', f"{tool_name}_project")
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