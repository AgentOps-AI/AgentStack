import os
import shutil
import unittest
from pathlib import Path
from agentstack import conf
from agentstack.inputs import InputsConfig, get_inputs, add_input_for_run
from agentstack.exceptions import ValidationError

BASE_PATH = Path(__file__).parent


class InputsConfigTest(unittest.TestCase):
    def setUp(self):
        self.framework = os.getenv('TEST_FRAMEWORK')
        self.project_dir = BASE_PATH / 'tmp' / self.framework / 'inputs_config'
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

    def test_yaml_error(self):
        # Create an invalid YAML file
        with open(self.project_dir / "src/config/inputs.yaml", 'w') as f:
            f.write("""
input_name: "This is a valid line"
invalid_yaml: "This line is missing a colon"
    nested_key: "This will cause a YAML error"
""")

        # Attempt to load the config, which should raise a ValidationError
        with self.assertRaises(ValidationError) as context:
            InputsConfig()

    def test_create_inputs_file_if_not_exists(self):
        # Ensure the inputs file doesn't exist
        inputs_file = self.project_dir / "src/config/inputs.yaml"
        if inputs_file.exists():
            inputs_file.unlink()

        # Create an InputsConfig instance and set a value
        with InputsConfig() as config:
            config['test_key'] = 'test_value'

        # Check that the file was created
        self.assertTrue(inputs_file.exists())

    def test_inputs_config_contains(self):
        # Create an InputsConfig instance and set some values
        with InputsConfig() as config:
            config['existing_key'] = 'some_value'
            config['another_key'] = 'another_value'

        # Test the __contains__ method
        self.assertTrue('existing_key' in config)
        self.assertTrue('another_key' in config)
        self.assertFalse('non_existing_key' in config)

    def test_get_inputs(self):
        # Set up some initial inputs
        with InputsConfig() as config:
            config['saved_key'] = 'saved_value'

        # Test get_inputs without run inputs
        inputs = get_inputs()
        self.assertEqual(inputs['saved_key'], 'saved_value')

        # Add a run input
        add_input_for_run('run_key', 'run_value')

        # Test get_inputs with run inputs
        inputs = get_inputs()
        self.assertEqual(inputs['saved_key'], 'saved_value')
        self.assertEqual(inputs['run_key'], 'run_value')

        # Test that run inputs override saved inputs
        add_input_for_run('saved_key', 'overridden_value')
        inputs = get_inputs()
        self.assertEqual(inputs['saved_key'], 'overridden_value')
