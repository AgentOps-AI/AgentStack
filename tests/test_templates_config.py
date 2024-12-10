import json
import unittest
from pathlib import Path
from agentstack.proj_templates import TemplateConfig, get_all_template_names, get_all_template_paths

BASE_PATH = Path(__file__).parent


class TemplateConfigTest(unittest.TestCase):
    def test_all_configs_from_template_name(self):
        for template_name in get_all_template_names():
            config = TemplateConfig.from_template_name(template_name)
            assert config.name == template_name
            # We can assume that pydantic validation caught any other issues

    def test_all_configs_from_template_path(self):
        for path in get_all_template_paths():
            config = TemplateConfig.from_json(path)
            assert config.name == path.stem
            # We can assume that pydantic validation caught any other issues
