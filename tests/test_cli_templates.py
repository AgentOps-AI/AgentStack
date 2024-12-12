import subprocess
import os, sys
import unittest
from parameterized import parameterized
from pathlib import Path
import shutil
from agentstack.proj_templates import get_all_template_names

BASE_PATH = Path(__file__).parent
CLI_ENTRY = [
    sys.executable,
    "-m",
    "agentstack.main",
]


class CLITemplatesTest(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path(BASE_PATH / 'tmp/cli_templates')
        os.makedirs(self.project_dir)
        os.chdir(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def _run_cli(self, *args):
        """Helper method to run the CLI with arguments."""
        return subprocess.run([*CLI_ENTRY, *args], capture_output=True, text=True)

    @parameterized.expand([(x,) for x in get_all_template_names()])
    def test_init_command_for_template(self, template_name):
        """Test the 'init' command to create a project directory with a template."""
        result = self._run_cli('init', 'test_project', '--template', template_name)
        self.assertEqual(result.returncode, 0)
        self.assertTrue((self.project_dir / 'test_project').exists())

    def test_export_template_v1(self):
        result = self._run_cli('init', f"test_project")
        self.assertEqual(result.returncode, 0)
        os.chdir(self.project_dir / f"test_project")
        result = self._run_cli('generate', 'agent', 'test_agent', '--llm', 'opeenai/gpt-4o')
        self.assertEqual(result.returncode, 0)
        result = self._run_cli('generate', 'task', 'test_task', '--agent', 'test_agent')
        self.assertEqual(result.returncode, 0)
        result = self._run_cli('tools', 'add', 'ftp', '--agents', 'test_agent')
        self.assertEqual(result.returncode, 0)

        result = self._run_cli('export', 'test_template.json')
        print(result.stdout)
        print(result.stderr)
        self.assertEqual(result.returncode, 0)
        self.assertTrue((self.project_dir / 'test_project/test_template.json').exists())
        template_str = (self.project_dir / 'test_project/test_template.json').read_text()
        self.maxDiff = None
        self.assertEqual(
            template_str,
            """{
    "name": "test_project",
    "description": "New agentstack project",
    "template_version": 2,
    "framework": "crewai",
    "method": "sequential",
    "agents": [
        {
            "name": "test_agent",
            "role": "Add your role here",
            "goal": "Add your goal here",
            "backstory": "Add your backstory here",
            "model": "opeenai/gpt-4o"
        }
    ],
    "tasks": [
        {
            "name": "test_task",
            "description": "Add your description here",
            "expected_output": "Add your expected_output here",
            "agent": "test_agent"
        }
    ],
    "tools": [
        {
            "name": "upload_files",
            "agents": [
                "test_agent"
            ]
        }
    ],
    "inputs": {}
}""",
        )
