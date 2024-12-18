import os
import shutil
import unittest
from pathlib import Path
from agentstack import conf
from agentstack.inputs import InputsConfig

BASE_PATH = Path(__file__).parent


class InputsConfigTest(unittest.TestCase):
    def setUp(self):
        self.project_dir = BASE_PATH / "tmp/inputs_config"
        os.makedirs(self.project_dir)
        os.makedirs(self.project_dir / "src/config")

        conf.set_path(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def test_minimal_input_config(self):
        shutil.copy(BASE_PATH / "fixtures/inputs_min.yaml", self.project_dir / "src/config/inputs.yaml")
        config = InputsConfig()
        assert config.to_dict() == {}

    def test_maximal_input_config(self):
        shutil.copy(BASE_PATH / "fixtures/inputs_max.yaml", self.project_dir / "src/config/inputs.yaml")
        config = InputsConfig()
        assert config['input_name'] == "This in an input"
        assert config['input_name_2'] == "This is another input"
        assert config.to_dict() == {'input_name': "This in an input", 'input_name_2': "This is another input"}
