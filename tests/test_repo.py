import unittest
import os, sys
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from agentstack import conf, log
from agentstack import repo
from agentstack.exceptions import EnvironmentError
import git


BASE_PATH = Path(__file__).parent

class TestRepo(unittest.TestCase):
    def setUp(self):
        self.framework = os.getenv('TEST_FRAMEWORK')
        self.test_dir = BASE_PATH / 'tmp' / self.framework / 'test_repo'
        self.test_dir.mkdir(parents=True, exist_ok=True)
        conf.set_path(self.test_dir)
        
        # get log output
        conf.DEBUG = True
        log.set_stdout(sys.stdout)
        log.set_stderr(sys.stderr)

    def tearDown(self):
        # Clean up test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def _init_repo(self):
        (self.test_dir / '.gitkeep').touch()  # git repo can't be empty
        repo.init()

    def test_init(self):
        if (self.test_dir / '.git').exists():
            shutil.rmtree(self.test_dir / '.git')

        self._init_repo()
        
        # Check if a git repository was created
        self.assertTrue((self.test_dir / '.git').is_dir())

        # Check if the repository has the correct initial branch
        git_repo = git.Repo(self.test_dir)
        self.assertEqual(git_repo.active_branch.name, repo.MAIN_BRANCH_NAME)

        # Check if an initial commit was made
        commits = list(git_repo.iter_commits())
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0].message, f"{repo.INITIAL_COMMIT_MESSAGE}{repo.AUTOMATION_NOTE}")

    def test_get_repo_nonexistent(self):
        if (self.test_dir / '.git').exists():
            shutil.rmtree(self.test_dir / '.git')

        with self.assertRaises(EnvironmentError):
            repo._get_repo()

    def test_get_repo_existent(self):
        self._init_repo()

        result = repo._get_repo()
        self.assertIsInstance(result, git.Repo)
        self.assertEqual(result.working_tree_dir, str(self.test_dir))

    def test_get_uncommitted_files_new_file(self):
        self._init_repo()

        new_file = self.test_dir / "new_file.txt"
        new_file.touch()

        # Check if the new file is in the list
        uncommitted = repo.get_uncommitted_files()
        self.assertIn("new_file.txt", uncommitted)

    def test_get_uncommitted_files_modified_file(self):
        self._init_repo()

        # Create and commit an initial file
        initial_file = self.test_dir / "initial_file.txt"
        initial_file.write_text("Initial content")
        
        with repo.Transaction() as transaction:
            transaction.add_message("Add initial file")

        # Modify the file
        initial_file.write_text("Modified content")

        # Check if the modified file is in the list
        uncommitted = repo.get_uncommitted_files()
        self.assertIn("initial_file.txt", uncommitted)

    def test_transaction_context_manager(self):
        self._init_repo()
        mock_commit = MagicMock()
        
        with patch('agentstack.repo.commit', mock_commit):
            with repo.Transaction() as transaction:
                (self.test_dir / "test_file.txt").touch()
                transaction.add_message("Test message")
                
                assert repo.get_uncommitted_files() == ["test_file.txt"]
            
            mock_commit.assert_called_once_with(f"Test message", automated=True)

    def test_transaction_multiple_messages(self):
        self._init_repo()
        mock_commit = MagicMock()
        
        with patch('agentstack.repo.commit', mock_commit):
            with repo.Transaction() as transaction:
                (self.test_dir / "test_file.txt").touch()
                transaction.add_message("First message")
                (self.test_dir / "test_file_2.txt").touch()
                transaction.add_message("Second message")
                
                assert repo.get_uncommitted_files() == ["test_file.txt", "test_file_2.txt"]
            
            mock_commit.assert_called_once_with(f"First message\nSecond message", automated=True)

    def test_transaction_no_changes(self):
        self._init_repo()
        mock_commit = MagicMock()
        
        with patch('agentstack.repo.commit', mock_commit):
            with repo.Transaction() as transaction:
                transaction.add_message("No changes")
                
                assert repo.get_uncommitted_files() == []
            
            mock_commit.assert_called_once_with(f"No changes", automated=True)

