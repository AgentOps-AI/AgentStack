import subprocess
import sys
import unittest
from pathlib import Path
import shutil


class TestAgentStackCLI(unittest.TestCase):
    CLI_ENTRY = [sys.executable, "-m", "agentstack.main"]  # Replace with your actual CLI entry point if different

    def run_cli(self, *args):
        """Helper method to run the CLI with arguments."""
        result = subprocess.run(
            [*self.CLI_ENTRY, *args],
            capture_output=True,
            text=True
        )
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
        test_dir = Path("test_project")

        # Ensure the directory doesn't exist from previous runs
        if test_dir.exists():
            shutil.rmtree(test_dir)

        result = self.run_cli("init", str(test_dir), "--no-wizard")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(test_dir.exists())

        # Clean up
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    unittest.main()
