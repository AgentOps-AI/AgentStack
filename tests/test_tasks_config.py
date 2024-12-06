import json
import os, sys
import shutil
import unittest
import importlib.resources
from pathlib import Path
from agentstack.tasks import TaskConfig, TASKS_FILENAME

BASE_PATH = Path(__file__).parent


class AgentConfigTest(unittest.TestCase):
    def setUp(self):
        self.project_dir = BASE_PATH / 'tmp/task_config'
        os.makedirs(self.project_dir / 'src/config')

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def test_empty_file(self):
        config = TaskConfig("task_name", self.project_dir)
        assert config.name == "task_name"
        assert config.description is ""
        assert config.expected_output is ""
        assert config.agent is ""

    def test_read_minimal_yaml(self):
        shutil.copy(BASE_PATH / "fixtures/tasks_min.yaml", self.project_dir / TASKS_FILENAME)
        config = TaskConfig("task_name", self.project_dir)
        assert config.name == "task_name"
        assert config.description is ""
        assert config.expected_output is ""
        assert config.agent is ""

    def test_read_maximal_yaml(self):
        shutil.copy(BASE_PATH / "fixtures/tasks_max.yaml", self.project_dir / TASKS_FILENAME)
        config = TaskConfig("task_name", self.project_dir)
        assert config.name == "task_name"
        assert config.description == "Add your description here"
        assert config.expected_output == "Add your expected output here"
        assert config.agent == "default_agent"

    def test_write_yaml(self):
        with TaskConfig("task_name", self.project_dir) as config:
            config.description = "Add your description here"
            config.expected_output = "Add your expected output here"
            config.agent = "default_agent"

        yaml_src = open(self.project_dir / TASKS_FILENAME).read()
        assert (
            yaml_src
            == """task_name:
  description: >-
    Add your description here
  expected_output: >-
    Add your expected output here
  agent: >-
    default_agent
"""
        )

    def test_write_none_values(self):
        with TaskConfig("task_name", self.project_dir) as config:
            config.description = None
            config.expected_output = None
            config.agent = None

        yaml_src = open(self.project_dir / TASKS_FILENAME).read()
        assert (
            yaml_src
            == """task_name:
  description: >
  expected_output: >
  agent: >
"""
        )
