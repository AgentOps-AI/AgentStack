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
        
    def setUp(self):
        self.TEST_DIR = Path("test_project")

    def run_cli(self, *args, cwd=None):
        """Helper method to run the CLI with arguments."""
        result = subprocess.run(
            [*self.CLI_ENTRY, *args],
            capture_output=True,
            text=True,
            cwd=cwd
        )
        return result
    
    # TODO: this is definitely not a clean way to test the CLI and
    # TODO: should be done more elegantly. For now, this allows
    # TODO: the tests to run sequentially and maintain state between
    # TODO: them without creating conflicting projects.
    def test_project_build_command(self):
        """Test the 'init' command to create a project directory."""
        # Ensure the directory doesn't exist from previous runs
        if self.TEST_DIR.exists():
            shutil.rmtree(self.TEST_DIR)

        result = self.run_cli("init", str(self.TEST_DIR), "--no-wizard")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.TEST_DIR.exists())

        """Test the 'generate agent' command."""
        agent_name = "test_agent"
        result = self.run_cli("generate", "agent", agent_name, cwd=self.TEST_DIR)
        self.assertEqual(result.returncode, 0)
        # Verify that the agent is added to agents.yaml
        agents_config = self.TEST_DIR / Path("src/config/agents.yaml")
        self.assertTrue(agents_config.exists())
        with open(agents_config, 'r') as f:
            content = f.read()
            self.assertIn(agent_name, content)

        """Test the 'generate task' command."""
        task_name = "test_task"
        result = self.run_cli("generate", "task", task_name, cwd=self.TEST_DIR)
        self.assertEqual(result.returncode, 0)
        # Verify that the task is added to tasks.yaml
        tasks_config = self.TEST_DIR /Path("src/config/tasks.yaml")
        self.assertTrue(tasks_config.exists())
        with open(tasks_config, 'r') as f:
            content = f.read()
            self.assertIn(task_name, content)

        """Test the 'tools list' command."""
        result = self.run_cli("tools", "list", cwd=self.TEST_DIR)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Available AgentStack Tools:", result.stdout)

        """Test the 'tools add' command."""
        tool_name = "ftp"
        result = self.run_cli("tools", "add", tool_name, cwd=self.TEST_DIR)
        self.assertEqual(result.returncode, 0)
        self.assertIn(f"Tool {tool_name} added", result.stdout)
        # Clean up: remove the tool
        self.run_cli("tools", "remove", tool_name)

        """Test the 'run' command."""
        result = self.run_cli("run", cwd=self.TEST_DIR)
        self.assertEqual(result.returncode, 0)

        # Clean up
        shutil.rmtree(self.TEST_DIR)

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
