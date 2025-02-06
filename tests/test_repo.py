import unittest
import os, sys
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from agentstack import conf
from agentstack import repo
from agentstack.exceptions import EnvironmentError
import git


BASE_PATH = Path(__file__).parent


class TestRepo(unittest.TestCase):
    def setUp(self):
        self.framework = os.getenv('TEST_FRAMEWORK')
        self.test_dir = BASE_PATH / 'tmp' / self.framework / 'test_repo'
        os.makedirs(self.test_dir)
        os.chdir(self.test_dir)  # gitpython needs a cwd
        
        conf.set_path(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_init(self):
        repo.init()

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
        with self.assertRaises(EnvironmentError):
            repo._get_repo()

    def test_get_repo_existent(self):
        repo.init()

        result = repo._get_repo()
        self.assertIsInstance(result, git.Repo)
        self.assertEqual(result.working_tree_dir, str(self.test_dir))

    def test_get_uncommitted_files_new_file(self):
        repo.init()

        new_file = self.test_dir / "new_file.txt"
        new_file.touch()

        # Check if the new file is in the list
        uncommitted = repo.get_uncommitted_files()
        self.assertIn("new_file.txt", uncommitted)

    def test_get_uncommitted_files_modified_file(self):
        repo.init()

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
        repo.init()
        mock_commit = MagicMock()

        with patch('agentstack.repo.commit', mock_commit):
            with repo.Transaction() as transaction:
                (self.test_dir / "test_file.txt").touch()
                transaction.add_message("Test message")

            mock_commit.assert_called_once_with(f"Test message", ["test_file.txt"], automated=True)

    def test_transaction_multiple_messages(self):
        repo.init()
        mock_commit = MagicMock()

        with patch('agentstack.repo.commit', mock_commit):
            with repo.Transaction() as transaction:
                (self.test_dir / "test_file.txt").touch()
                transaction.add_message("First message")
                (self.test_dir / "test_file_2.txt").touch()
                transaction.add_message("Second message")

            mock_commit.assert_called_once_with(
                f"First message, Second message", ["test_file.txt", "test_file_2.txt"], automated=True
            )

    def test_transaction_no_changes(self):
        repo.init()
        mock_commit = MagicMock()

        with patch('agentstack.repo.commit', mock_commit):
            with repo.Transaction() as transaction:
                transaction.add_message("No changes")

                assert repo.get_uncommitted_files() == []

            mock_commit.assert_not_called()
