import os
import unittest
from unittest.mock import patch, Mock, mock_open
from pathlib import Path
import tempfile
import zipfile

from agentstack.deploy import deploy, collect_files, create_zip_in_memory, get_project_id, load_pyproject

class TestDeployFunctions(unittest.TestCase):
    def setUp(self):
        # Common setup for tests
        self.bearer_token = "test_token"
        self.project_id = "test_project_123"

    @patch('agentstack.deploy.get_stored_token')
    @patch('agentstack.deploy.login')
    @patch('agentstack.deploy.get_project_id')
    @patch('agentstack.deploy.requests.post')
    @patch('agentstack.deploy.webbrowser.open')
    def test_deploy_success(self, mock_browser, mock_post, mock_get_project, mock_login, mock_token):
        # Setup mocks
        mock_token.return_value = self.bearer_token
        mock_get_project.return_value = self.project_id
        mock_post.return_value.status_code = 200

        # Call deploy function
        deploy()

        # Verify API call
        mock_post.assert_called_once()
        self.assertIn('/deploy/build', mock_post.call_args[0][0])
        self.assertIn('Bearer test_token', mock_post.call_args[1]['headers']['Authorization'])

        # Verify browser opened
        mock_browser.assert_called_once_with(f"http://localhost:5173/project/{self.project_id}")

    @patch('agentstack.deploy.get_stored_token')
    @patch('agentstack.deploy.login')
    def test_deploy_no_auth(self, mock_login, mock_token):
        # Setup mocks for failed authentication
        mock_token.return_value = None
        mock_login.return_value = False

        # Call deploy function
        deploy()

        # Verify login was attempted
        mock_login.assert_called_once()
        mock_token.assert_called_once()

    def test_collect_files(self):
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, 'test.py').touch()
            Path(tmpdir, 'test.toml').touch()
            Path(tmpdir, 'ignore.txt').touch()

            # Create subdirectory with files
            subdir = Path(tmpdir, 'subdir')
            subdir.mkdir()
            Path(subdir, 'sub.py').touch()

            # Create excluded directory
            venv = Path(tmpdir, '.venv')
            venv.mkdir()
            Path(venv, 'venv.py').touch()

            # Collect files
            files = collect_files(tmpdir, ('.py', '.toml'))

            # Verify results
            file_names = {f.name for f in files}
            self.assertIn('test.py', file_names)
            self.assertIn('test.toml', file_names)
            self.assertIn('sub.py', file_names)
            self.assertNotIn('ignore.txt', file_names)
            self.assertNotIn('venv.py', file_names)

    @patch('agentstack.deploy.requests.post')
    def test_get_project_id_create_new(self, mock_post):
        # Mock successful project creation
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'id': 'new_project_123'}

        # Mock ConfigFile
        with patch('agentstack.deploy.ConfigFile') as mock_config:
            mock_config.return_value.hosted_project_id = None
            mock_config.return_value.project_name = 'test_project'

            project_id = get_project_id()

            self.assertEqual(project_id, 'new_project_123')
            mock_post.assert_called_once()

    def test_load_pyproject(self):
        # Test with valid pyproject.toml
        mock_toml_content = b'''
        [project]
        name = "test-project"
        version = "1.0.0"
        '''

        mock_file = mock_open(read_data=mock_toml_content)
        with patch('builtins.open', mock_file):
            with patch('os.path.exists') as mock_exists:
                mock_exists.return_value = True
                result = load_pyproject()

                # Verify file was opened in binary mode
                mock_file.assert_called_once_with("pyproject.toml", "rb")

                self.assertIsNotNone(result)
                self.assertIn('project', result)
                self.assertEqual(result['project']['name'], 'test-project')

    @patch('agentstack.deploy.log.error')
    def test_create_zip_in_memory(self, mock_log):
        # Create temporary test files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test directory structure
            test_dir = Path(tmpdir)
            test_file = test_dir / 'test.py'
            test_file.write_text('print("test")')

            # Create mock spinner
            mock_spinner = Mock()

            # Test zip creation
            # We'll need to change to the temp directory to maintain correct relative paths
            original_dir = Path.cwd()
            try:
                os.chdir(tmpdir)
                # Now use relative path for the file
                files = [Path('test.py')]
                zip_file = create_zip_in_memory(files, mock_spinner)

                # Verify zip contents
                with zipfile.ZipFile(zip_file, 'r') as zf:
                    self.assertIn('test.py', zf.namelist())
                    # Additional verification of zip contents
                    self.assertEqual(len(zf.namelist()), 1)
                    with zf.open('test.py') as f:
                        content = f.read().decode('utf-8')
                        self.assertEqual(content, 'print("test")')
            finally:
                # Make sure we always return to the original directory
                os.chdir(original_dir)
