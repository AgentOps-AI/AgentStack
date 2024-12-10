from pathlib import Path
import json
import unittest
from parameterized import parameterized
from agentstack.proj_templates import TemplateConfig, get_all_template_names, get_all_template_paths

BASE_PATH = Path(__file__).parent


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
