import subprocess
import os, sys
import unittest
from pathlib import Path
import shutil
from cli_test_utils import run_cli

BASE_PATH = Path(__file__).parent


class TestAgentStackCLI(unittest.TestCase):

    def test_version(self):
        """Test the --version command."""
        result = run_cli("--version")
        self.assertEqual(result.returncode, 0)
        self.assertIn("AgentStack CLI version:", result.stdout)

    def test_invalid_command(self):
        """Test an invalid command gracefully exits."""
        result = run_cli("invalid_command")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage:", result.stderr)

    def test_run_command_invalid_project(self):
        """Test the 'run' command on an invalid project."""
        test_dir = Path(BASE_PATH / 'tmp/test_project')
        if test_dir.exists():
            shutil.rmtree(test_dir, ignore_errors=True)
        os.makedirs(test_dir)

        # Write a basic agentstack.json file
        with (test_dir / 'agentstack.json').open('w') as f:
            f.write(open(BASE_PATH / 'fixtures/agentstack.json', 'r').read())

        os.chdir(test_dir)
        result = run_cli('run')
        self.assertEqual(result.returncode, 1)
        self.assertIn("An error occurred", result.stderr)

        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
