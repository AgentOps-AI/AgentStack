import os
import unittest
from pathlib import Path
import shutil
from agentstack import conf
from agentstack.conf import ConfigFile
from agentstack.generation.files import EnvFile
from agentstack.utils import (
    verify_agentstack_project,
    get_framework,
    get_telemetry_opt_out,
    get_version,
)

BASE_PATH = Path(__file__).parent


# TODO copy files to working directory
class GenerationFilesTest(unittest.TestCase):
    def setUp(self):
        self.framework = os.getenv('TEST_FRAMEWORK')
        self.project_dir = BASE_PATH / 'tmp' / self.framework / 'generation_files'
        os.makedirs(self.project_dir)

        shutil.copy(BASE_PATH / "fixtures/agentstack.json", self.project_dir / "agentstack.json")
        conf.set_path(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def test_read_config(self):
        config = ConfigFile()  # + agentstack.json
        assert config.framework == "crewai"
        assert config.tools == []
        assert config.telemetry_opt_out is None
        assert config.default_model is None
        assert config.agentstack_version == get_version()
        assert config.template is None
        assert config.template_version is None
        assert config.use_git is True

    def test_write_config(self):
        with ConfigFile() as config:
            config.framework = "crewai"
            config.tools = ["tool1", "tool2"]
            config.telemetry_opt_out = True
            config.default_model = "openai/gpt-4o"
            config.agentstack_version = "0.2.1"
            config.template = "default"
            config.template_version = "1"
            config.use_git = False

        tmp_data = open(self.project_dir / "agentstack.json").read()
        assert (
            tmp_data
            == """{
    "framework": "crewai",
    "tools": [
        "tool1",
        "tool2"
    ],
    "telemetry_opt_out": true,
    "default_model": "openai/gpt-4o",
    "agentstack_version": "0.2.1",
    "template": "default",
    "template_version": "1",
    "use_git": false
}"""
        )

    def test_read_missing_config(self):
        conf.set_path(BASE_PATH / "missing")
        with self.assertRaises(FileNotFoundError) as _:
            _ = ConfigFile()

    def test_verify_agentstack_project_valid(self):
        verify_agentstack_project()

    def test_verify_agentstack_project_invalid(self):
        conf.set_path(BASE_PATH / "missing")
        with self.assertRaises(Exception) as _:
            verify_agentstack_project()

    def test_get_framework(self):
        assert get_framework() == "crewai"

    def test_get_framework_missing(self):
        conf.set_path(BASE_PATH / "missing")
        with self.assertRaises(Exception) as _:
            get_framework()

    def test_read_env(self):
        shutil.copy(BASE_PATH / "fixtures/.env", self.project_dir / ".env")

        env = EnvFile()
        assert env.variables == {"ENV_VAR1": "value1", "ENV_VAR2": "value2", "ENV_VAR3": "12a34b===="}
        assert env["ENV_VAR1"] == "value1"
        assert env["ENV_VAR2"] == "value2"
        assert env["ENV_VAR3"] == "12a34b===="
        with self.assertRaises(KeyError) as _:
            env["ENV_VAR100"]

    def test_write_env(self):
        shutil.copy(BASE_PATH / "fixtures/.env", self.project_dir / ".env")

        with EnvFile() as env:
            env.append_if_new("ENV_VAR1", "value100")  # Should not be updated
            env.append_if_new("ENV_VAR100", "value2")  # Should be added

        tmp_data = open(self.project_dir / ".env").read()
        assert (
            tmp_data
            == """\nENV_VAR1=value1\nENV_VAR2=value_ignored\nENV_VAR2=value2\nENV_VAR3 = \"12a34b====\"\n#ENV_VAR4=""\nENV_VAR100=value2"""
        )
    
    def test_write_env_numeric_that_can_be_boolean(self):
        shutil.copy(BASE_PATH / "fixtures/.env", self.project_dir / ".env")

        with EnvFile() as env:
            env.append_if_new("ENV_VAR100", 0)
            env.append_if_new("ENV_VAR101", 1)
        
        env = EnvFile()  # re-read the file
        assert env.variables == {"ENV_VAR1": "value1", "ENV_VAR2": "value2", "ENV_VAR3": "12a34b====", "ENV_VAR100": "0", "ENV_VAR101": "1"}

    def test_write_env_commented(self):
        """We should be able to write a commented-out value."""
        shutil.copy(BASE_PATH / "fixtures/.env", self.project_dir / ".env")

        with EnvFile() as env:
            env.append_if_new("ENV_VAR4", "value3")

        env = EnvFile()  # re-read the file
        assert env.variables == {"ENV_VAR1": "value1", "ENV_VAR2": "value2", "ENV_VAR3": "12a34b====", "ENV_VAR4": "value3"}

        tmp_file = open(self.project_dir / ".env").read()
        assert (
            tmp_file
            == """\nENV_VAR1=value1\nENV_VAR2=value_ignored\nENV_VAR2=value2\nENV_VAR3 = \"12a34b====\"\n#ENV_VAR4=""\nENV_VAR4=value3"""
        )
