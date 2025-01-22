import unittest
import os
import json
from unittest.mock import patch, mock_open
from parameterized import parameterized
from pathlib import Path
from packaging.version import Version
import requests
from agentstack.update import (
    _is_ci_environment,
    CI_ENV_VARS,
    should_update,
    get_latest_version,
    AGENTSTACK_PACKAGE,
    load_update_data,
    record_update_check,
    INSTALL_PATH,
    CHECK_EVERY,
)

BASE_DIR = Path(__file__).parent


class TestUpdate(unittest.TestCase):
    @patch.dict('os.environ', {}, clear=True)
    def test_is_ci_environment_false(self):
        """
        Test that _is_ci_environment() returns False when no CI environment variables are set.
        """
        self.assertFalse(_is_ci_environment())

    @parameterized.expand([(var,) for var in CI_ENV_VARS])
    @patch.dict('os.environ', clear=True)
    def test_is_ci_environment_true(self, env_var):
        """
        Test that _is_ci_environment() returns True when any CI environment variable is set.
        """
        with patch.dict('os.environ', {env_var: 'true'}):
            self.assertTrue(_is_ci_environment())

    def test_updates_disabled_by_env_var_in_test(self):
        """
        Test that should_update() returns False when AGENTSTACK_UPDATE_DISABLE environment variable is set to 'true'.
        """
        with patch.dict('os.environ', {'AGENTSTACK_UPDATE_DISABLE': 'true'}):
            self.assertFalse(should_update())

    def test_get_latest_version(self):
        """
        Test that get_latest_version returns a valid Version object from the actual PyPI.
        """
        latest_version = get_latest_version(AGENTSTACK_PACKAGE)
        self.assertIsInstance(latest_version, Version)

    @patch('requests.get')
    def test_get_latest_version_404(self, mock_get):
        """
        Test that get_latest_version raises an exception when the request returns a 404.
        """
        mock_response = mock_get.return_value
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Client Error")

        with self.assertRaises(Exception) as context:
            get_latest_version(AGENTSTACK_PACKAGE)

    @patch('requests.get')
    def test_get_latest_version_timeout(self, mock_get):
        """
        Test that get_latest_version handles request timeouts.
        """
        mock_get.side_effect = requests.Timeout("Request timed out")

        with self.assertRaises(Exception) as context:
            get_latest_version(AGENTSTACK_PACKAGE)

    @patch(
        'agentstack.update.LAST_CHECK_FILE_PATH',
        new_callable=lambda: BASE_DIR / 'tests/tmp/test_update/last_check.json',
    )
    @patch('agentstack.update.time.time')
    @patch('agentstack.update._is_ci_environment')
    def test_record_update_check(self, mock_is_ci, mock_time, mock_file_path):
        """
        Test that record_update_check correctly saves the current timestamp.
        """
        mock_is_ci.return_value = False
        mock_time.return_value = 1234567890.0

        record_update_check()

        with open(mock_file_path, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, {str(INSTALL_PATH): 1234567890.0})

        os.remove(mock_file_path)
        mock_file_path.parent.rmdir()

    @patch('agentstack.update.Path.exists')
    def test_load_update_data_empty(self, mock_exists):
        """
        Test that load_update_data returns an empty dict when the file doesn't exist.
        """
        mock_exists.return_value = False
        data = load_update_data()
        self.assertEqual(data, {})

    @patch('builtins.open', new_callable=mock_open)
    @patch('agentstack.update.Path.exists')
    def test_load_update_data_valid(self, mock_exists, mock_file):
        """
        Test that load_update_data correctly loads data from a valid file.
        """
        mock_exists.return_value = True
        test_data = {"test_path": 1234567890.0}
        mock_file.return_value.read.return_value = json.dumps(test_data)

        data = load_update_data()
        self.assertEqual(data, test_data)

    @patch.dict('os.environ', {}, clear=True)  # clear env to remove AGENTSTACK_UPDATE_DISABLE
    @patch('agentstack.update.time.time')
    @patch('agentstack.update._is_ci_environment')
    @patch('agentstack.update.load_update_data')
    def test_should_update(self, mock_load_data, mock_is_ci, mock_time):
        # Test CI environment
        mock_is_ci.return_value = True
        self.assertTrue(should_update())

        # Test first run (no data)
        mock_is_ci.return_value = False
        mock_load_data.return_value = {}
        self.assertTrue(should_update())

        # Test recent check
        mock_time.return_value = 1000000
        mock_load_data.return_value = {str(INSTALL_PATH): 999999}  # 1 second ago
        self.assertFalse(should_update())

        # Test old check
        mock_load_data.return_value = {
            str(INSTALL_PATH): 1000000 - CHECK_EVERY - 1
        }  # CHECK_EVERY + 1 second ago
        self.assertTrue(should_update())
