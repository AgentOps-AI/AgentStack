import json
import os, sys
import shutil
import unittest
import importlib.resources
from pathlib import Path
from agentstack import conf
from agentstack.agents import AgentConfig, AGENTS_FILENAME

BASE_PATH = Path(__file__).parent


class AgentConfigTest(unittest.TestCase):
    def setUp(self):
        self.project_dir = BASE_PATH / 'tmp/agent_config'
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
        assert config.llm == "provider/model"

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
