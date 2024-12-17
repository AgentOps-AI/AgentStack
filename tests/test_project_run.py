import os
from pathlib import Path
import shutil
import unittest
from parameterized import parameterized_class

from agentstack import conf
from agentstack.conf import ConfigFile
from agentstack import frameworks
from agentstack.cli import run_project
from agentstack.generation import project_generation

BASE_PATH = Path(__file__).parent


@parameterized_class([{"framework": framework} for framework in frameworks.SUPPORTED_FRAMEWORKS])
class ProjectRunTest(unittest.TestCase):
    def setUp(self):
        self.project_dir = BASE_PATH / 'tmp/project_run' / self.framework

        # Generate project using the proper template
        project_generation.generate_project(
            project_dir=self.project_dir,
            framework=self.framework,
            project_name="Test Project",
            project_slug="test-project"
        )

        # set the framework in agentstack.json
        shutil.copy(BASE_PATH / 'fixtures' / 'agentstack.json', self.project_dir / 'agentstack.json')
        conf.set_path(self.project_dir)
        with ConfigFile() as config:
            config.framework = self.framework

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
