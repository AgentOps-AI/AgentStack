from pathlib import Path
import json
import unittest
import os
import shutil
from unittest.mock import patch
from parameterized import parameterized
from agentstack.exceptions import ValidationError
from agentstack.templates import (
    CURRENT_VERSION, 
    TemplateConfig,
    get_all_template_names,
    get_all_template_paths,
    get_all_templates,
)

BASE_PATH = Path(__file__).parent
VALID_TEMPLATE_URL = "https://raw.githubusercontent.com/AgentOps-AI/AgentStack/13a6e335fb163b932ed037562fcedbc269f0d5a5/agentstack/templates/proj_templates/content_creator.json"
INVALID_TEMPLATE_URL = "https://raw.githubusercontent.com/AgentOps-AI/AgentStack/13a6e335fb163b932ed037562fcedbc269f0d5a5/tests/fixtures/tool_config_min.json"


class TemplateConfigTest(unittest.TestCase):
    def setUp(self):
        self.framework = os.getenv('TEST_FRAMEWORK')
        self.project_dir = BASE_PATH / 'tmp' / self.framework / 'template_config'
        os.makedirs(self.project_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    @parameterized.expand([(x,) for x in get_all_template_names()])
    def test_all_configs_from_template_name(self, template_name: str):
        config = TemplateConfig.from_template_name(template_name)
        assert config.name == template_name
        # We can assume that pydantic validation caught any other issues

    @parameterized.expand([(x,) for x in get_all_template_paths()])
    def test_all_configs_from_template_path(self, template_path: Path):
        config = TemplateConfig.from_file(template_path)
        assert config.name == template_path.stem
        # We can assume that pydantic validation caught any other issues

    def test_invalid_template_name(self):
        with self.assertRaises(ValidationError):
            TemplateConfig.from_template_name("invalid")

    def test_load_template_from_valid_url(self):
        config = TemplateConfig.from_url(VALID_TEMPLATE_URL)
        assert config.name == "content_creator"

    def load_template_from_invalid_url(self):
        with self.assertRaises(ValidationError):
            TemplateConfig.from_url(INVALID_TEMPLATE_URL)

    def test_write_to_file_with_json_suffix(self):
        config = TemplateConfig.from_template_name("content_creator")
        file_path = self.project_dir / "test_template.json"
        config.write_to_file(file_path)

        # Check if file exists
        self.assertTrue(file_path.exists())

        # Read the file and check if it's valid JSON
        with open(file_path, 'r') as f:
            written_data = json.load(f)

        # Compare written data with original config
        self.assertEqual(written_data["name"], config.name)
        self.assertEqual(written_data["description"], config.description)
        self.assertEqual(written_data["template_version"], config.template_version)

    def test_write_to_file_without_suffix(self):
        config = TemplateConfig.from_template_name("content_creator")
        file_path = self.project_dir / "test_template"
        config.write_to_file(file_path)

        # Check if file exists with .json suffix
        expected_path = file_path.with_suffix('.json')
        self.assertTrue(expected_path.exists())

        # Read the file and check if it's valid JSON
        with open(expected_path, 'r') as f:
            written_data = json.load(f)

        # Compare written data with original config
        self.assertEqual(written_data["name"], config.name)
        self.assertEqual(written_data["description"], config.description)
        self.assertEqual(written_data["template_version"], config.template_version)

    def test_from_user_input_url(self):
        config = TemplateConfig.from_user_input(VALID_TEMPLATE_URL)
        self.assertEqual(config.name, "content_creator")
        self.assertEqual(config.template_version, CURRENT_VERSION)

    def test_from_user_input_name(self):
        config = TemplateConfig.from_user_input('content_creator')
        self.assertEqual(config.name, "content_creator")
        self.assertEqual(config.template_version, CURRENT_VERSION)

    def test_from_user_input_local_file(self):
        test_file = self.project_dir / 'test_local_template.json'

        test_data = {
            "name": "test_local",
            "description": "Test local file",
            "template_version": 3,
            "framework": "test",
            "method": "test",
            "manager_agent": None,
            "agents": [],
            "tasks": [],
            "tools": [],
            "inputs": {},
        }

        with open(test_file, 'w') as f:
            json.dump(test_data, f, indent=2)

        config = TemplateConfig.from_user_input(str(test_file))
        self.assertEqual(config.name, "test_local")
        self.assertEqual(config.template_version, CURRENT_VERSION)

    def test_from_file_missing_file(self):
        non_existent_path = Path("/path/to/non_existent_file.json")
        with self.assertRaises(ValidationError) as context:
            TemplateConfig.from_file(non_existent_path)

    def test_from_url_invalid_url(self):
        invalid_url = "not_a_valid_url"
        with self.assertRaises(ValidationError) as context:
            TemplateConfig.from_url(invalid_url)

    @patch('agentstack.templates.requests.get')
    def test_from_url_non_200_response(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 404

        invalid_url = "https://example.com/non_existent_template.json"
        with self.assertRaises(ValidationError) as context:
            TemplateConfig.from_url(invalid_url)
        mock_get.assert_called_once_with(invalid_url)

    def test_from_json_invalid_version(self):
        invalid_template = {
            "name": "invalid_version_template",
            "description": "A template with an invalid version",
            "template_version": 999,  # Invalid version
            "framework": "test",
            "method": "test",
            "manager_agent": None,
            "agents": [],
            "tasks": [],
            "tools": [],
            "inputs": {},
        }
        with self.assertRaises(ValidationError) as context:
            TemplateConfig.from_json(invalid_template)

    def test_from_json_pydantic_validation_error(self):
        invalid_template = {
            "name": "invalid_template",
            "description": "A template with invalid data",
            "template_version": CURRENT_VERSION,
            "framework": "test",
            "method": "test",
            "manager_agent": None,
            "agents": [
                {
                    "name": "Invalid Agent",
                    "role": "Tester",
                    "goal": "Test invalid data",
                    "backstory": "This agent has an invalid model",
                    "allow_delegation": False,
                    "model": 123,  # This should be a string, not an integer
                }
            ],
            "tasks": [],
            "tools": [],
            "inputs": {},
        }
        with self.assertRaises(ValidationError) as context:
            TemplateConfig.from_json(invalid_template)

    def test_from_file_invalid_json(self):
        temp_file = self.project_dir / 'invalid_template.json'
        with open(temp_file, 'w') as f:
            f.write("This is not valid JSON")

        try:
            with self.assertRaises(ValidationError) as context:
                TemplateConfig.from_file(temp_file)
        finally:
            os.unlink(temp_file)

    @patch('agentstack.templates.requests.get')
    def test_from_url_invalid_json(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        invalid_url = "https://example.com/invalid_json_template.json"
        with self.assertRaises(ValidationError) as context:
            TemplateConfig.from_url(invalid_url)
        mock_get.assert_called_once_with(invalid_url)

    def test_get_all_templates(self):
        for template in get_all_templates():
            self.assertIsInstance(template, TemplateConfig)

    def test_get_all_template_names(self):
        for name in get_all_template_names():
            self.assertIsInstance(name, str)

    def test_get_all_template_paths(self):
        for path in get_all_template_paths():
            self.assertIsInstance(path, Path)

    @patch('agentstack.templates.get_package_path')
    @patch('pathlib.Path.iterdir')
    def test_get_all_template_paths_no_json_files(self, mock_iterdir, mock_get_package_path):
        mock_get_package_path.return_value = Path('/mock/path')
        mock_iterdir.return_value = [Path('file1.txt'), Path('file2.csv')]  # No JSON files

        paths = get_all_template_paths()

        self.assertEqual(paths, [])
        mock_get_package_path.assert_called_once()
        mock_iterdir.assert_called_once()
