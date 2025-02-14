import os
import shutil
import json
import re
from pathlib import Path
import unittest
from unittest.mock import MagicMock, PropertyMock, patch
from parameterized import parameterized
from agentstack import conf
from agentstack.exceptions import ValidationError
from agentstack._tools import (
    ToolConfig, 
    get_tool, 
    get_all_tools, 
    get_all_tool_paths, 
    get_all_tool_names, 
    UserToolConfig, 
    get_permissions, 
    ToolPermission, 
    Action, 
)

BASE_PATH = Path(__file__).parent

class ToolConfigTest(unittest.TestCase):
    def setUp(self):
        self.framework = os.getenv('TEST_FRAMEWORK')
        self.project_dir = BASE_PATH / 'tmp' / self.framework / 'test_tool_config'
        os.makedirs(self.project_dir)
        os.makedirs(self.project_dir / 'src/config')
        
        shutil.copy(BASE_PATH / "fixtures/agentstack.json", self.project_dir / "agentstack.json")
        conf.set_path(self.project_dir)
        with conf.ConfigFile() as config:
            config.framework = self.framework

    def tearDown(self):
        shutil.rmtree(self.project_dir)
    
    def test_minimal_json(self):
        config = ToolConfig.from_json(BASE_PATH / "fixtures/tool_config_min.json")
        assert config.name == "tool_name"
        assert config.category == "category"
        assert config.tool_names == ["tool1", "tool2"]
        # TODO test config.tools
        assert config.url is None
        assert config.cta is None
        assert config.env is None
        assert config.post_install is None
        assert config.post_remove is None

    def test_maximal_json(self):
        config = ToolConfig.from_json(BASE_PATH / "fixtures/tool_config_max.json")
        assert config.name == "tool_name"
        assert config.category == "category"
        assert config.tool_names == ["tool1", "tool2", "tool3"]
        # TODO test config.tools
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

    @parameterized.expand([(x, ) for x in get_all_tools()])
    def test_all_tools(self, config: ToolConfig):
        assert isinstance(config, ToolConfig)
        # We can assume that pydantic validation caught any other issues

    def test_load_invalid_tool(self):
        with self.assertRaises(ValidationError):
            ToolConfig.from_tool_name("invalid_tool")

    def test_load_invalid_config(self):
        with self.assertRaises(ValidationError):
            ToolConfig.from_json(BASE_PATH / "fixtures/tool_config_invalid.json")

    @parameterized.expand([(x, ) for x in get_all_tool_paths()])
    def test_all_json_configs_from_tool_path(self, path):
        try:
            config = ToolConfig.from_json(f"{path}/config.json")
        except json.decoder.JSONDecodeError:
            raise Exception(
                f"Failed to decode tool json at {path}. Does your tool config fit the required formatting? "
                "https://github.com/AgentOps-AI/AgentStack/blob/main/agentstack/tools/~README.md"
            )

        assert config.name == path.stem

    @patch('agentstack._tools.ToolConfig.module_name', new_callable=PropertyMock)
    def test_config_module_missing_function(self, mock_module_name):
        mock_module_name.return_value = 'tests.fixtures.test_tool'
        with self.assertRaises(ValidationError):
            config = ToolConfig.from_json(BASE_PATH / "fixtures/tool_config_min.json")
            config.module

    @patch('agentstack._tools.ToolConfig.module_name', new_callable=PropertyMock)
    def test_config_module_missing_import(self, mock_module_name):
        mock_module_name.return_value = 'invalid'
        with self.assertRaises(ValidationError):
            config = ToolConfig.from_json(BASE_PATH / "fixtures/tool_config_min.json")
            config.module

    @parameterized.expand([(x, ) for x in get_all_tool_names()])
    def test_user_tool_config_uninitialized(self, tool_name):
        with self.assertRaises(FileNotFoundError):
            UserToolConfig(tool_name)

    def test_user_tool_config_initialize(self):
        test_tools = get_all_tools()[:3]  # just a few
        with conf.ConfigFile() as config:
            config.tools = [tool.name for tool in test_tools]
        
        assert not UserToolConfig.exists()
        UserToolConfig.initialize()
        
        assert UserToolConfig.exists()
        for tool in test_tools:
            user_conf = UserToolConfig(tool.name)
            assert user_conf.tools.keys() == tool.tools.keys()
            assert user_conf.tools.keys() == tool.allowed_tools.keys()
            assert user_conf.tool_names == tool.tool_names
            assert user_conf.tool_names == tool.allowed_tool_names
    
    def test_user_tool_config_customize(self):
        shutil.copy(BASE_PATH / "fixtures/tools.yaml", self.project_dir / "src/config/tools.yaml")
        test_tool = ToolConfig.from_json(BASE_PATH / "fixtures/tool_config_max.json")
        user_conf = UserToolConfig(test_tool.name)
        
        # tool has `tool1`, `tool2`, `tool3`
        # user has `tool1`, `tool2`
        assert user_conf.tool_names == test_tool.allowed_tool_names
        assert user_conf.tool_names != test_tool.tool_names
        assert user_conf.tools['tool1'].actions == [Action.EXECUTE]
        assert user_conf.tools['tool2'] is None
        
        assert test_tool.allowed_tools['tool1'].actions == [Action.EXECUTE]
        assert test_tool.allowed_tools['tool1'].additional_property == "value"
        assert test_tool.allowed_tools['tool2'].actions == [Action.READ]
        assert not hasattr(test_tool.allowed_tools, 'tool3')
    
    @patch('agentstack._tools._get_user_tool_config_path')
    def test_load_invalid_user_config(self, mock_get_user_tool_config_path):
        mock_get_user_tool_config_path.return_value = BASE_PATH / "fixtures/tools_invalid.yaml"
        with self.assertRaises(ValidationError):
            UserToolConfig('tool_name')
    
    @patch('agentstack._tools._get_user_tool_config_path')
    def test_load_malformed_user_config(self, mock_get_user_tool_config_path):
        mock_get_user_tool_config_path.return_value = BASE_PATH / "fixtures/malformed.yaml"
        with self.assertRaises(ValidationError):
            UserToolConfig('tool_name')
    
    def test_tool_permission_rwe(self):
        tool_permission = ToolPermission(actions=['read', 'write', 'execute'])
        assert tool_permission.READ
        assert tool_permission.WRITE
        assert tool_permission.EXECUTE
    
    def test_tool_permission_attrs(self):
        tool_permission = ToolPermission(actions=['read'], foo='bar', baz='qux')
        assert tool_permission.foo == 'bar'
        assert tool_permission.baz == 'qux'
        assert tool_permission.undefined is None
    
    def test_get_permissions(self):
        from agentstack._tools.file_read import read_file
        permissions = get_permissions(read_file)
        assert isinstance(permissions, ToolPermission)

    def test_tool_missing(self):
        with self.assertRaises(ValidationError):
            ToolConfig.from_tool_name("non_existent_tool")

    def test_from_custom_path(self):
        os.mkdir(self.project_dir / "src/tools/my_custom_tool")
        shutil.copy(BASE_PATH / "fixtures/tool_config_custom.json", 
            self.project_dir / "src/tools/my_custom_tool/config.json")

        config = ToolConfig.from_tool_name("my_custom_tool")
        assert config.module_name == "src.tools.my_custom_tool"
