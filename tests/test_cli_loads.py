import subprocess
import os, sys
import unittest
from pathlib import Path
import shutil

BASE_PATH = Path(__file__).parent


class TestAgentStackCLI(unittest.TestCase):
    # Replace with your actual CLI entry point if different
    CLI_ENTRY = [
        sys.executable,
        "-m",
        "agentstack.main",
    ]

    def run_cli(self, *args):
        """Helper method to run the CLI with arguments."""
        result = subprocess.run([*self.CLI_ENTRY, *args], capture_output=True, text=True)
        return result

    def test_version(self):
        """Test the --version command."""
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0)
        self.assertIn("AgentStack CLI version:", result.stdout)

    def test_invalid_command(self):
        """Test an invalid command gracefully exits."""
        result = self.run_cli("invalid_command")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage:", result.stderr)

    def test_init_command(self):
        """Test the 'init' command to create a project directory."""
        test_dir = Path(BASE_PATH / 'tmp/test_project')

        # Ensure the directory doesn't exist from previous runs
        if test_dir.exists():
            shutil.rmtree(test_dir)
        os.makedirs(test_dir)

        os.chdir(test_dir)
        result = self.run_cli("init", str(test_dir))
        self.assertEqual(result.returncode, 0)
        self.assertTrue(test_dir.exists())

        # Clean up
        shutil.rmtree(test_dir)

    def test_run_command_invalid_project(self):
        """Test the 'run' command on an invalid project."""
        test_dir = Path(BASE_PATH / 'tmp/test_project')
        if test_dir.exists():
            shutil.rmtree(test_dir)
        os.makedirs(test_dir)

        # Write a basic agentstack.json file
        with (test_dir / 'agentstack.json').open('w') as f:
            f.write(open(BASE_PATH / 'fixtures/agentstack.json', 'r').read())

        os.chdir(test_dir)
        result = self.run_cli('run')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Project validation failed", result.stdout)

        shutil.rmtree(test_dir)


if __name__ == "__main__":
    unittest.main()
