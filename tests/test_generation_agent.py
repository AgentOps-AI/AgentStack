import os, sys
from pathlib import Path
import shutil
import unittest
import ast

from agentstack.conf import ConfigFile, set_path
from agentstack import frameworks
from agentstack.exceptions import ValidationError
from agentstack.agents import AGENTS_FILENAME
from agentstack.tasks import TASKS_FILENAME
from agentstack.generation.agent_generation import add_agent

BASE_PATH = Path(__file__).parent


class TestGenerationAgent(unittest.TestCase):
    def setUp(self):
        self.framework = os.getenv('TEST_FRAMEWORK')
        self.project_dir = BASE_PATH / 'tmp' / self.framework / 'agent_generation'

        os.makedirs(self.project_dir)
        os.makedirs(self.project_dir / 'src')
        os.makedirs(self.project_dir / 'src' / 'config')
        (self.project_dir / 'src' / '__init__.py').touch()

        # copy agents.yaml and tasks.yaml
        shutil.copy(BASE_PATH / 'fixtures/agents_max.yaml', self.project_dir / AGENTS_FILENAME)
        shutil.copy(BASE_PATH / 'fixtures/tasks_max.yaml', self.project_dir / TASKS_FILENAME)

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

    def test_add_agent(self):
        add_agent(
            'test_agent_two',
            role='role',
            goal='goal',
            backstory='backstory',
            llm='openai/gpt-4o',
        )

        entrypoint_path = frameworks.get_entrypoint_path(self.framework)
        entrypoint_src = open(entrypoint_path).read()
        # agents.yaml is covered in test_agents_config.py
        # TODO framework-specific validation for code structure
        assert 'def test_agent_two' in entrypoint_src
        # verify that the file's syntax is valid with ast
        ast.parse(entrypoint_src)

    def test_add_agent_exists(self):
        with self.assertRaises(Exception) as context:
            add_agent(
                'agent_name',
                role='role',
                goal='goal',
                backstory='backstory',
                llm='openai/gpt-4o',
            )
