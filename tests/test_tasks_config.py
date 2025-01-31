import json
import os, sys
import shutil
import unittest
import importlib.resources
from pathlib import Path
from agentstack import conf
from agentstack.tasks import TaskConfig, TASKS_FILENAME, get_all_task_names, get_all_tasks
from agentstack.exceptions import ValidationError

BASE_PATH = Path(__file__).parent


class AgentConfigTest(unittest.TestCase):
    def setUp(self):
        self.framework = os.getenv('TEST_FRAMEWORK')
        self.project_dir = BASE_PATH / 'tmp' / self.framework / 'task_config'
        os.makedirs(self.project_dir / 'src/config')
        conf.set_path(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def test_empty_file(self):
        config = TaskConfig("task_name")
        assert config.name == "task_name"
        assert config.description == ""
        assert config.expected_output == ""
        assert config.agent == ""

    def test_read_minimal_yaml(self):
        shutil.copy(BASE_PATH / "fixtures/tasks_min.yaml", self.project_dir / TASKS_FILENAME)
        config = TaskConfig("task_name")
        assert config.name == "task_name"
        assert config.description == ""
        assert config.expected_output == ""
        assert config.agent == ""

    def test_read_maximal_yaml(self):
        shutil.copy(BASE_PATH / "fixtures/tasks_max.yaml", self.project_dir / TASKS_FILENAME)
        config = TaskConfig("task_name")
        assert config.name == "task_name"
        assert config.description == "Add your description here"
        assert config.expected_output == "Add your expected output here"
        assert config.agent == "default_agent"

    def test_write_yaml(self):
        with TaskConfig("task_name") as config:
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
        with TaskConfig("task_name") as config:
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

    def test_yaml_error(self):
        # Create an invalid YAML file
        with open(self.project_dir / TASKS_FILENAME, 'w') as f:
            f.write("""
task_name:
  description: "This is a valid line"
  invalid_yaml: "This line is missing a colon"
    nested_key: "This will cause a YAML error"
""")

        # Attempt to load the config, which should raise a ValidationError
        with self.assertRaises(ValidationError) as context:
            TaskConfig("task_name")

    def test_pydantic_validation_error(self):
        # Create a YAML file with an invalid field type
        with open(self.project_dir / TASKS_FILENAME, 'w') as f:
            f.write("""
task_name:
  description: "This is a valid description"
  expected_output: "This is a valid expected output"
  agent: 123  # This should be a string, not an integer
""")

        # Attempt to load the config, which should raise a ValidationError
        with self.assertRaises(ValidationError) as context:
            TaskConfig("task_name")

    def test_get_all_task_names(self):
        shutil.copy(BASE_PATH / "fixtures/tasks_max.yaml", self.project_dir / TASKS_FILENAME)

        task_names = get_all_task_names()
        self.assertEqual(set(task_names), {"task_name", "task_name_two"})
        self.assertEqual(task_names, ["task_name", "task_name_two"])

    def test_get_all_task_names_missing_file(self):
        if os.path.exists(self.project_dir / TASKS_FILENAME):
            os.remove(self.project_dir / TASKS_FILENAME)
        non_existent_file_task_names = get_all_task_names()
        self.assertEqual(non_existent_file_task_names, [])

    def test_get_all_task_names_empty_file(self):
        with open(self.project_dir / TASKS_FILENAME, 'w') as f:
            f.write("")
        
        empty_task_names = get_all_task_names()
        self.assertEqual(empty_task_names, [])

    def test_get_all_tasks(self):
        shutil.copy(BASE_PATH / "fixtures/tasks_max.yaml", self.project_dir / TASKS_FILENAME)
        for task in get_all_tasks():
            self.assertIsInstance(task, TaskConfig)
