import subprocess
import os, sys
import unittest
from parameterized import parameterized
from pathlib import Path
import shutil
from agentstack.tools import get_all_tool_names

BASE_PATH = Path(__file__).parent
CLI_ENTRY = [
    sys.executable,
    "-m",
    "agentstack.main",
]


# TODO parameterized framework
class CLIToolsTest(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path(BASE_PATH / 'tmp/cli_tools')
        os.makedirs(self.project_dir)
        os.chdir(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def _run_cli(self, *args):
        """Helper method to run the CLI with arguments."""
        return subprocess.run([*CLI_ENTRY, *args], capture_output=True, text=True)

    @parameterized.expand([(x,) for x in get_all_tool_names()])
    @unittest.skip("Dependency resolution issue")
    def test_add_tool(self, tool_name):
        """Test the adding every tool to a project."""
        result = self._run_cli('init', f"{tool_name}_project")
        self.assertEqual(result.returncode, 0)
        os.chdir(self.project_dir / f"{tool_name}_project")
        result = self._run_cli('generate', 'agent', 'test_agent', '--llm', 'opeenai/gpt-4o')
        self.assertEqual(result.returncode, 0)
        result = self._run_cli('generate', 'task', 'test_task')
        self.assertEqual(result.returncode, 0)

        result = self._run_cli('tools', 'add', tool_name)
        print(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.project_dir.exists())
