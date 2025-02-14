import json
import os, sys
import shutil
import unittest
from parameterized import parameterized
import importlib.resources
from pathlib import Path
from agentstack import conf
from agentstack import frameworks
from agentstack.agents import (
    AGENTS_FILENAME, 
    AgentConfig, 
    get_all_agent_names, 
    get_all_agents, 
    get_agent
)
from agentstack.exceptions import ValidationError

BASE_PATH = Path(__file__).parent


class AgentConfigTest(unittest.TestCase):
    def setUp(self):
        self.framework = os.getenv('TEST_FRAMEWORK')
        self.project_dir = BASE_PATH / 'tmp' / self.framework / 'test_agents_config'
        os.makedirs(self.project_dir)
        
        conf.set_path(self.project_dir)
        os.makedirs(self.project_dir / 'src/config')

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def test_empty_file(self):
        config = AgentConfig("agent_name")
        assert config.name == "agent_name"
        assert config.role == ""
        assert config.goal == ""
        assert config.backstory == ""
        assert config.llm == ""

    def test_read_minimal_yaml(self):
        shutil.copy(BASE_PATH / "fixtures/agents_min.yaml", self.project_dir / AGENTS_FILENAME)
        config = AgentConfig("agent_name")
        assert config.name == "agent_name"
        assert config.role == ""
        assert config.goal == ""
        assert config.backstory == ""
        assert config.llm == ""

    def test_read_maximal_yaml(self):
        shutil.copy(BASE_PATH / "fixtures/agents_max.yaml", self.project_dir / AGENTS_FILENAME)
        config = AgentConfig("agent_name")
        assert config.name == "agent_name"
        assert config.role == "role"
        assert config.goal == "this is a goal"
        assert config.backstory == "backstory"
        assert config.llm == "openai/gpt-4o"

    def test_write_yaml(self):
        with AgentConfig("agent_name") as config:
            config.role = "role"
            config.goal = "this is a goal"
            config.backstory = "backstory"
            config.llm = "provider/model"

        yaml_src = open(self.project_dir / AGENTS_FILENAME).read()
        assert (
            yaml_src
            == """agent_name:
  role: >-
    role
  goal: >-
    this is a goal
  backstory: >-
    backstory
  llm: provider/model
"""
        )

    def test_write_none_values(self):
        with AgentConfig("agent_name") as config:
            config.role = None
            config.goal = None
            config.backstory = None
            config.llm = None

        yaml_src = open(self.project_dir / AGENTS_FILENAME).read()
        assert (
            yaml_src
            == """agent_name:
  role: >
  goal: >
  backstory: >
  llm:
"""
        )

    def test_yaml_error(self):
        # Create an invalid YAML file
        with open(self.project_dir / AGENTS_FILENAME, 'w') as f:
            f.write("""
agent_name:
  role: "This is a valid line"
  invalid_yaml: "This line is missing a colon"
    nested_key: "This will cause a YAML error"
""")

        # Attempt to load the config, which should raise a ValidationError
        with self.assertRaises(ValidationError) as context:
            AgentConfig("agent_name")

    def test_pydantic_validation_error(self):
        # Create a YAML file with an invalid field type
        with open(self.project_dir / AGENTS_FILENAME, 'w') as f:
            f.write("""
agent_name:
  role: "This is a valid role"
  goal: "This is a valid goal"
  backstory: "This is a valid backstory"
  llm: 123  # This should be a string, not an integer
""")

        # Attempt to load the config, which should raise a ValidationError
        with self.assertRaises(ValidationError) as context:
            AgentConfig("agent_name")

    def test_get_all_agent_names(self):
        shutil.copy(BASE_PATH / "fixtures/agents_max.yaml", self.project_dir / AGENTS_FILENAME)

        agent_names = get_all_agent_names()
        self.assertEqual(set(agent_names), {"agent_name", "second_agent_name"})
        self.assertEqual(agent_names, ["agent_name", "second_agent_name"])

    def test_get_all_agent_names_missing_file(self):
        if os.path.exists(self.project_dir / AGENTS_FILENAME):
            os.remove(self.project_dir / AGENTS_FILENAME)
        non_existent_file_agent_names = get_all_agent_names()
        self.assertEqual(non_existent_file_agent_names, [])

    def test_get_all_agent_names_empty_file(self):
        with open(self.project_dir / AGENTS_FILENAME, 'w') as f:
            f.write("")
        
        empty_agent_names = get_all_agent_names()
        self.assertEqual(empty_agent_names, [])

    def test_get_all_agents(self):
        shutil.copy(BASE_PATH / "fixtures/agents_max.yaml", self.project_dir / AGENTS_FILENAME)

        for agent in get_all_agents():
            self.assertIsInstance(agent, AgentConfig)

    def test_get_agent(self):
        shutil.copy(BASE_PATH / "fixtures/agents_max.yaml", self.project_dir / AGENTS_FILENAME)

        agent = get_agent("agent_name")
        self.assertIsInstance(agent, AgentConfig)
        self.assertEqual(agent.name, "agent_name")
    
    def test_get_agent_prompt(self):
        shutil.copy(BASE_PATH / "fixtures/agents_max.yaml", self.project_dir / AGENTS_FILENAME)

        agent = get_agent("agent_name")
        assert agent.role in agent.prompt
        assert agent.goal in agent.prompt
        assert agent.backstory in agent.prompt

    @parameterized.expand([(x, ) for x in frameworks.SUPPORTED_FRAMEWORKS])
    @unittest.mock.patch("agentstack.frameworks.get_framework")
    def test_get_agent_model_provider(self, framework, mock_get_framework):
        mock_get_framework.return_value = framework
        shutil.copy(BASE_PATH / "fixtures/agents_max.yaml", self.project_dir / AGENTS_FILENAME)

        agent = get_agent("agent_name")
        assert agent.llm == "openai/gpt-4o"
        assert agent.provider == "openai"
        assert agent.model == "gpt-4o"