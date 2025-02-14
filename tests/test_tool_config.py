import os
import json
import unittest
import re
from pathlib import Path
import shutil
from agentstack import conf
from agentstack.exceptions import ValidationError
from agentstack._tools import ToolConfig, get_all_tool_paths, get_all_tool_names

BASE_PATH = Path(__file__).parent

class ToolConfigTest(unittest.TestCase):
    def setUp(self):
        self.project_dir = BASE_PATH / 'tmp' / 'tool_config'
        os.makedirs(self.project_dir)
        os.makedirs(self.project_dir / 'src')
        os.makedirs(self.project_dir / 'src' / 'tools')
        conf.set_path(self.project_dir)
    
    def tearDown(self):
        shutil.rmtree(self.project_dir)
    
    def test_minimal_json(self):
        config = ToolConfig.from_json(BASE_PATH / "fixtures/tool_config_min.json")
        assert config.name == "tool_name"
        assert config.category == "category"
        assert config.tools == ["tool1", "tool2"]
        assert config.url is None
        assert config.cta is None
        assert config.env is None
        assert config.post_install is None
        assert config.post_remove is None

    def test_maximal_json(self):
        config = ToolConfig.from_json(BASE_PATH / "fixtures/tool_config_max.json")
        assert config.name == "tool_name"
        assert config.category == "category"
        assert config.tools == ["tool1", "tool2"]
        assert config.url == "https://example.com"
        assert config.cta == "Click me!"
        assert config.env == {"ENV_VAR1": "value1", "ENV_VAR2": "value2"}
        assert config.post_install == "install.sh"
        assert config.post_remove == "remove.sh"

    def test_invalid_json(self):
        with self.assertRaises(ValidationError):
            ToolConfig.from_json(BASE_PATH / "fixtures/agentstack.json")

    def test_write_to_file(self):
        config = ToolConfig.from_json(BASE_PATH / "fixtures/tool_config_min.json")
        config.write_to_file(self.project_dir / "config.json")
        assert (self.project_dir / "config.json").exists()
        read_config = ToolConfig.from_json(self.project_dir / "config.json")
        assert read_config == config

    def test_write_to_file_invalid_suffix(self):
        config = ToolConfig.from_json(BASE_PATH / "fixtures/tool_config_min.json")
        with self.assertRaises(ValidationError):
            config.write_to_file(self.project_dir / "config.txt")

    def test_dependency_versions(self):
        """Test that all dependencies specify a version constraint."""
        for tool_name in get_all_tool_names():
            config = ToolConfig.from_tool_name(tool_name)

            if hasattr(config, 'dependencies') and config.dependencies:
                version_pattern = r'[><=~!]=|[@><=~!]'
                for dep in config.dependencies:
                    if not re.search(version_pattern, dep):
                        raise AssertionError(
                            f"Dependency '{dep}' in {config.name} does not specify a version constraint. "
                            "All dependencies must include version specifications."
                        )

    def test_all_json_configs_from_tool_name(self):
        for tool_name in get_all_tool_names():
            config = ToolConfig.from_tool_name(tool_name)
            assert config.name == tool_name
            # We can assume that pydantic validation caught any other issues

    def test_all_json_configs_from_tool_path(self):
        for path in get_all_tool_paths():
            try:
                config = ToolConfig.from_json(f"{path}/config.json")
            except json.decoder.JSONDecodeError:
                raise Exception(
                    f"Failed to decode tool json at {path}. Does your tool config fit the required formatting? "
                    "https://github.com/AgentOps-AI/AgentStack/blob/main/agentstack/tools/~README.md"
                )

            assert config.name == path.stem

    def test_tool_missing(self):
        with self.assertRaises(ValidationError):
            ToolConfig.from_tool_name("non_existent_tool")

    def test_from_custom_path(self):
        os.mkdir(self.project_dir / "src/tools/my_custom_tool")
        shutil.copy(BASE_PATH / "fixtures/tool_config_custom.json", 
            self.project_dir / "src/tools/my_custom_tool/config.json")

        config = ToolConfig.from_tool_name("my_custom_tool")
        assert config.module_name == "src.tools.my_custom_tool"