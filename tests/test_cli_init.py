import os, sys
import unittest
from parameterized import parameterized
from pathlib import Path
import shutil
from cli_test_utils import run_cli
from agentstack.proj_templates import get_all_templates

BASE_PATH = Path(__file__).parent

class CLIInitTest(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path(BASE_PATH / 'tmp/cli_init')
        os.chdir(BASE_PATH)  # Change to parent directory first
        os.makedirs(self.project_dir, exist_ok=True)
        os.chdir(self.project_dir)
        # Force UTF-8 encoding for the test environment
        os.environ['PYTHONIOENCODING'] = 'utf-8'

    def tearDown(self):
        shutil.rmtree(self.project_dir, ignore_errors=True)

    @parameterized.expand([(template.name, ) for template in get_all_templates()])
    def test_init_command(self, template_name: str):
        """Test the 'init' command to create a project directory."""
        result = run_cli('init', 'test_project', '--template', template_name)
        self.assertEqual(result.returncode, 0)
        self.assertTrue((self.project_dir / 'test_project').exists())
