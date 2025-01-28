import os
import unittest
import uuid
from unittest.mock import patch, mock_open

from agentstack.telemetry import _get_cli_user_guid
from agentstack.utils import get_telemetry_opt_out

class TelemetryTest(unittest.TestCase):
    def test_telemetry_opt_out_env_var_set(self):
        AGENTSTACK_TELEMETRY_OPT_OUT = os.getenv("AGENTSTACK_TELEMETRY_OPT_OUT")
        assert AGENTSTACK_TELEMETRY_OPT_OUT

    def test_telemetry_opt_out_set_in_test_environment(self):
        assert get_telemetry_opt_out()

    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='existing-guid')
    def test_existing_guid_file(self, mock_file, mock_exists):
        """Test when GUID file exists and can be read successfully"""
        mock_exists.return_value = True

        result = _get_cli_user_guid()

        self.assertEqual(result, 'existing-guid')
        mock_exists.assert_called_once_with()

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    @patch('uuid.uuid4')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_new_guid(self, mock_file, mock_uuid, mock_mkdir, mock_exists):
        """Test creation of new GUID when file doesn't exist"""
        mock_exists.return_value = False
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')

        result = _get_cli_user_guid()

        self.assertEqual(result, '12345678-1234-5678-1234-567812345678')
        mock_exists.assert_called_once_with()
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        handle = mock_file()
        handle.write.assert_called_once_with('12345678-1234-5678-1234-567812345678')

    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    def test_permission_error_on_read(self, mock_file, mock_exists):
        """Test handling of PermissionError when reading file"""
        mock_exists.return_value = True
        mock_file.side_effect = PermissionError()

        result = _get_cli_user_guid()

        self.assertEqual(result, 'unknown')
        mock_exists.assert_called_once_with()

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open')
    def test_permission_error_on_write(self, mock_file, mock_mkdir, mock_exists):
        """Test handling of PermissionError when writing new file"""
        mock_exists.return_value = False
        mock_file.side_effect = PermissionError()

        result = _get_cli_user_guid()

        self.assertEqual(result, 'unknown')
        mock_exists.assert_called_once_with()
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    def test_os_error_on_mkdir(self, mock_mkdir, mock_exists):
        """Test handling of OSError when creating directory"""
        mock_exists.return_value = False
        mock_mkdir.side_effect = OSError()

        result = _get_cli_user_guid()

        self.assertEqual(result, 'unknown')
        mock_exists.assert_called_once_with()
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)