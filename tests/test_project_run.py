import os
from pathlib import Path
import shutil
import unittest

from agentstack import conf
from agentstack.conf import ConfigFile
from agentstack import frameworks
from agentstack.cli import run_project

BASE_PATH = Path(__file__).parent


class ProjectRunTest(unittest.TestCase):
    def setUp(self):
        self.framework = os.getenv('TEST_FRAMEWORK')
        self.project_dir = BASE_PATH / 'tmp' / self.framework / 'project_run'

        os.makedirs(self.project_dir)
        os.makedirs(self.project_dir / 'src')
        (self.project_dir / 'src' / '__init__.py').touch()

        with open(self.project_dir / 'src' / 'main.py', 'w') as f:
            f.write('def run(): pass')

        # set the framework in agentstack.json
        shutil.copy(BASE_PATH / 'fixtures' / 'agentstack.json', self.project_dir / 'agentstack.json')
        conf.set_path(self.project_dir)
        with ConfigFile() as config:
            config.framework = self.framework

        # populate the entrypoint
        entrypoint_path = frameworks.get_entrypoint_path(self.framework)
        shutil.copy(BASE_PATH / f"fixtures/frameworks/{self.framework}/entrypoint_max.py", entrypoint_path)

        # write a basic .env file
        shutil.copy(BASE_PATH / 'fixtures' / '.env', self.project_dir / '.env')

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def test_run_project(self):
        run_project()

    def test_env_is_set(self):
        """
        After running a project, the environment variables should be set from project_dir/.env.
        """
        run_project()
        assert os.getenv('ENV_VAR1') == 'value1'
