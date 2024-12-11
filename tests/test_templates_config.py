from pathlib import Path
import json
import unittest
from parameterized import parameterized
from agentstack import ValidationError
from agentstack.proj_templates import TemplateConfig, get_all_template_names, get_all_template_paths

BASE_PATH = Path(__file__).parent
VALID_TEMPLATE_URL = "https://raw.githubusercontent.com/AgentOps-AI/AgentStack/13a6e335fb163b932ed037562fcedbc269f0d5a5/agentstack/templates/proj_templates/content_creator.json"
INVALID_TEMPLATE_URL = "https://raw.githubusercontent.com/AgentOps-AI/AgentStack/13a6e335fb163b932ed037562fcedbc269f0d5a5/tests/fixtures/tool_config_min.json"


class TemplateConfigTest(unittest.TestCase):
    @parameterized.expand([(x,) for x in get_all_template_names()])
    def test_all_configs_from_template_name(self, template_name: str):
        config = TemplateConfig.from_template_name(template_name)
        assert config.name == template_name
        # We can assume that pydantic validation caught any other issues

    @parameterized.expand([(x,) for x in get_all_template_paths()])
    def test_all_configs_from_template_path(self, template_path: Path):
        config = TemplateConfig.from_json(template_path)
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
