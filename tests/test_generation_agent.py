import os, sys
from pathlib import Path
import shutil
import unittest
from parameterized import parameterized_class
import ast

from agentstack import frameworks, ValidationError
from agentstack.generation.files import ConfigFile
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

        # populate the entrypoint
        entrypoint_path = frameworks.get_entrypoint_path(self.framework, self.project_dir)
        shutil.copy(BASE_PATH / f"fixtures/frameworks/{self.framework}/entrypoint_max.py", entrypoint_path)

        # set the framework in agentstack.json
        shutil.copy(BASE_PATH / 'fixtures' / 'agentstack.json', self.project_dir / 'agentstack.json')
        with ConfigFile(self.project_dir) as config:
            config.framework = self.framework

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def test_add_agent(self):
        add_agent(
            'test_agent_two',
            role='role',
            goal='goal',
            backstory='backstory',
            llm='llm',
            path=self.project_dir,
        )

        entrypoint_path = frameworks.get_entrypoint_path(self.framework, self.project_dir)
        entrypoint_src = open(entrypoint_path).read()
        # agents.yaml is covered in test_agents_config.py
        # TODO framework-specific validation for code structure
        assert 'def test_agent_two' in entrypoint_src
        # verify that the file's syntax is valid with ast
        ast.parse(entrypoint_src)

    def test_add_agent_exists(self):
        with self.assertRaises(SystemExit) as context:
            add_agent(
                'test_agent',
                role='role',
                goal='goal',
                backstory='backstory',
                llm='llm',
                path=self.project_dir,
            )
