import os, sys
from pathlib import Path
import shutil
import unittest
from parameterized import parameterized_class
import ast

from agentstack.conf import ConfigFile, set_path
from agentstack.exceptions import ValidationError
from agentstack import frameworks
from agentstack.tasks import TaskConfig
from agentstack.generation.task_generation import add_task
from agentstack.generation.agent_generation import add_agent

BASE_PATH = Path(__file__).parent


@parameterized_class([{"framework": framework} for framework in frameworks.SUPPORTED_FRAMEWORKS])
class TestGenerationAgent(unittest.TestCase):
    def setUp(self):
        self.project_dir = BASE_PATH / 'tmp' / 'agent_generation'

        os.makedirs(self.project_dir)
        os.makedirs(self.project_dir / 'src')
        os.makedirs(self.project_dir / 'src' / 'config')
        (self.project_dir / 'src' / '__init__.py').touch()

        # set the framework in agentstack.json
        shutil.copy(BASE_PATH / 'fixtures' / 'agentstack.json', self.project_dir / 'agentstack.json')
        set_path(self.project_dir)
        with ConfigFile() as config:
            config.framework = self.framework

        # populate the entrypoint
        entrypoint_path = frameworks.get_entrypoint_path(self.framework)
        shutil.copy(BASE_PATH / f"fixtures/frameworks/{self.framework}/entrypoint_max.py", entrypoint_path)

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def test_add_task(self):
        add_task(
            'task_test_two',
            description='description',
            expected_output='expected_output',
            agent='agent',
        )

        entrypoint_path = frameworks.get_entrypoint_path(self.framework)
        entrypoint_src = open(entrypoint_path).read()
        # agents.yaml is covered in test_agents_config.py
        # TODO framework-specific validation for code structure
        assert 'def task_test_two' in entrypoint_src
        # verify that the file's syntax is valid with ast
        ast.parse(entrypoint_src)

    def test_add_agent_exists(self):
        with self.assertRaises(SystemExit) as context:
            add_task(
                'test_task',
                description='description',
                expected_output='expected_output',
                agent='agent',
            )

    def test_add_task_selects_single_agent(self):
        add_task(
            'task_test',
            description='description',
            expected_output='expected_output',
        )

        task_config = TaskConfig('task_test')
        assert task_config.agent == 'test_agent'  # defined in entrypoint_max.py
