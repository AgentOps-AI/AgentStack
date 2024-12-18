import subprocess
import os, sys
import unittest
from parameterized import parameterized
from pathlib import Path
import shutil

BASE_PATH = Path(__file__).parent
CLI_ENTRY = [
    sys.executable,
    "-m",
    "agentstack.main",
]


class CLIInitTest(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path(BASE_PATH / 'tmp/cli_init')
        os.makedirs(self.project_dir)
        os.chdir(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def _run_cli(self, *args):
        """Helper method to run the CLI with arguments."""
        return subprocess.run([*CLI_ENTRY, *args], capture_output=True, text=True)

    def test_init_command(self):
        """Test the 'init' command to create a project directory."""
        result = self._run_cli('init', 'test_project')
        self.assertEqual(result.returncode, 0)
        self.assertTrue((self.project_dir / 'test_project').exists())
