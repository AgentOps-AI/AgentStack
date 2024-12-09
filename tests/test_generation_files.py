import os
import unittest
from pathlib import Path
import shutil
from agentstack.generation.files import ConfigFile, EnvFile
from agentstack.utils import (
    verify_agentstack_project,
    get_framework,
    get_telemetry_opt_out,
    get_version,
)

BASE_PATH = Path(__file__).parent


class GenerationFilesTest(unittest.TestCase):
    def test_read_config(self):
        config = ConfigFile(BASE_PATH / "fixtures")  # + agentstack.json
        assert config.framework == "crewai"
        assert config.tools == []
        assert config.telemetry_opt_out is None
        assert config.default_model is None
        assert config.agentstack_version == get_version()
        assert config.template is None
        assert config.template_version is None

    def test_write_config(self):
        try:
            os.makedirs(BASE_PATH / "tmp", exist_ok=True)
            shutil.copy(BASE_PATH / "fixtures/agentstack.json", BASE_PATH / "tmp/agentstack.json")

            with ConfigFile(BASE_PATH / "tmp") as config:
                config.framework = "crewai"
                config.tools = ["tool1", "tool2"]
                config.telemetry_opt_out = True
                config.default_model = "openai/gpt-4o"
                config.agentstack_version = "0.2.1"
                config.template = "default"
                config.template_version = "1"

            tmp_data = open(BASE_PATH / "tmp/agentstack.json").read()
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
    "template_version": "1"
}"""
            )
        except Exception as e:
            raise e
        finally:
            os.remove(BASE_PATH / "tmp/agentstack.json")
            # os.rmdir(BASE_PATH / "tmp")

    def test_read_missing_config(self):
        with self.assertRaises(FileNotFoundError) as _:
            _ = ConfigFile(BASE_PATH / "missing")

    def test_verify_agentstack_project_valid(self):
        verify_agentstack_project(BASE_PATH / "fixtures")

    def test_verify_agentstack_project_invalid(self):
        with self.assertRaises(SystemExit) as _:
            verify_agentstack_project(BASE_PATH / "missing")

    def test_get_framework(self):
        assert get_framework(BASE_PATH / "fixtures") == "crewai"
        with self.assertRaises(SystemExit) as _:
            get_framework(BASE_PATH / "missing")

    def test_read_env(self):
        env = EnvFile(BASE_PATH / "fixtures")
        assert env.variables == {"ENV_VAR1": "value1", "ENV_VAR2": "value2"}
        assert env["ENV_VAR1"] == "value1"
        assert env["ENV_VAR2"] == "value2"
        with self.assertRaises(KeyError) as _:
            env["ENV_VAR3"]

    def test_write_env(self):
        try:
            os.makedirs(BASE_PATH / "tmp", exist_ok=True)
            shutil.copy(BASE_PATH / "fixtures/.env", BASE_PATH / "tmp/.env")

            with EnvFile(BASE_PATH / "tmp") as env:
                env.append_if_new("ENV_VAR1", "value100")  # Should not be updated
                env.append_if_new("ENV_VAR100", "value2")  # Should be added

            tmp_data = open(BASE_PATH / "tmp/.env").read()
            assert tmp_data == """\nENV_VAR1=value1\nENV_VAR2=value2\nENV_VAR100=value2"""
        except Exception as e:
            raise e
        finally:
            os.remove(BASE_PATH / "tmp/.env")
            # os.rmdir(BASE_PATH / "tmp")
