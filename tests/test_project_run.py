import os
from pathlib import Path
import shutil
import unittest
from parameterized import parameterized_class

from agentstack import frameworks
from agentstack.cli import run_project
from agentstack.generation.files import ConfigFile

BASE_PATH = Path(__file__).parent


@parameterized_class([{"framework": framework} for framework in frameworks.SUPPORTED_FRAMEWORKS])
class ProjectRunTest(unittest.TestCase):
    def setUp(self):
        self.project_dir = BASE_PATH / 'tmp' / self.framework

        os.makedirs(self.project_dir)
        os.makedirs(self.project_dir / 'src')
        (self.project_dir / 'src' / '__init__.py').touch()

        with open(self.project_dir / 'src' / 'main.py', 'w') as f:
            f.write('def run(): pass')

        # set the framework in agentstack.json
        shutil.copy(BASE_PATH / 'fixtures' / 'agentstack.json', self.project_dir / 'agentstack.json')
        with ConfigFile(self.project_dir) as config:
            config.framework = self.framework

        # populate the entrypoint
        entrypoint_path = frameworks.get_entrypoint_path(self.framework, self.project_dir)
        shutil.copy(BASE_PATH / f"fixtures/frameworks/{self.framework}/entrypoint_max.py", entrypoint_path)

        # write a basic .env file
        shutil.copy(BASE_PATH / 'fixtures' / '.env', self.project_dir / '.env')

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def test_run_project(self):
        run_project(path=self.project_dir)

    def test_env_is_set(self):
        """
        After running a project, the environment variables should be set from project_dir/.env.
        """
        run_project(path=self.project_dir)
        assert os.getenv('ENV_VAR1') == 'value1'
