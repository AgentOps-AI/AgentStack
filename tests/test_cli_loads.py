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
    def test_generate_agent_command(self):
        """Test the 'generate agent' command."""
        agent_name = "test_agent"
        result = self.run_cli("generate", "agent", agent_name)
        self.assertEqual(result.returncode, 0)
        # Verify that the agent is added to agents.yaml
        agents_config = Path("src/config/agents.yaml")
        self.assertTrue(agents_config.exists())
        with open(agents_config, 'r') as f:
            content = f.read()
            self.assertIn(agent_name, content)

    def test_generate_task_command(self):
        """Test the 'generate task' command."""
        task_name = "test_task"
        result = self.run_cli("generate", "task", task_name)
        self.assertEqual(result.returncode, 0)
        # Verify that the task is added to tasks.yaml
        tasks_config = Path("src/config/tasks.yaml")
        self.assertTrue(tasks_config.exists())
        with open(tasks_config, 'r') as f:
            content = f.read()
            self.assertIn(task_name, content)

    def test_tools_list_command(self):
        """Test the 'tools list' command."""
        result = self.run_cli("tools", "list")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Available AgentStack Tools:", result.stdout)

    def test_tools_add_command(self):
        """Test the 'tools add' command."""
        tool_name = "example_tool"
        result = self.run_cli("tools", "add", tool_name)
        self.assertEqual(result.returncode, 0)
        self.assertIn(f"Tool {tool_name} added", result.stdout)
        # Clean up: remove the tool
        self.run_cli("tools", "remove", tool_name)

    def test_run_command(self):
        """Test the 'run' command."""
        result = self.run_cli("run")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Running your agent", result.stdout)


if __name__ == "__main__":
    unittest.main()
