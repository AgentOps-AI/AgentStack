import shutil
import git
from agentstack import conf, log
from agentstack.exceptions import EnvironmentError


MAIN_BRANCH_NAME = "main"

AUTOMATION_NOTE = "\n\n(This commit was made automatically by AgentStack)"
INITIAL_COMMIT_MESSAGE = f"Initial commit."


class Transaction:
    """
    A transaction for committing changes to a git repository.

    Use as a context manager:
    ```
    with Transaction() as transaction:
        Path('foo').touch()
        transaction.add_message("Created foo")
    ```

    Changes will be committed automatically on exit.
    """

    automated: bool
    messages: list[str]

    def __init__(self, automated: bool = True) -> None:
        self.automated = automated
        self.messages = []

    def commit(self) -> None:
        """Commit all changes to the repository."""
        commit('\n'.join(self.messages), automated=self.automated)
        self.messages = []

    def add_message(self, message: str) -> None:
        """Add a message to the commit."""
        self.messages.append(message)

    def __enter__(self) -> 'Transaction':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            log.error(f"git transaction was not completed due to an Exception")
            return
        self.commit()


def _require_git():
    """
    Raise an EnvironmentError if git is not installed.
    """
    try:
        assert shutil.which('git')
    except (AssertionError, ImportError):
        message = "git is not installed.\nIn order to track changes to files in your project, install git.\n"
        if shutil.which('apt'):
            message += "Hint: run `sudo apt install git`\n"
        elif shutil.which('brew'):
            message += "Hint: run `brew install git`\n"
        elif shutil.which('port'):
            message += "Hint: run `sudo port install git`\n"
        raise EnvironmentError(message)


def _get_repo() -> git.Repo:
    """
    Get the git repository for the current project.
    """
    _require_git()
    try:
        repo = git.Repo(conf.PATH.absolute())
        assert repo.active_branch.name == MAIN_BRANCH_NAME
        return repo
    except AssertionError:
        raise EnvironmentError(f"Git repository is not on the {MAIN_BRANCH_NAME} branch.")
    except git.exc.InvalidGitRepositoryError:
        raise EnvironmentError("No git repository found in the current project.")


def init() -> None:
    """
    Initialize a git repository for the current project if one does not exist
    and commit all changes.
    """
    try:
        _require_git()
    except EnvironmentError as e:
        log.warning(e)
        return

    # creates a new repo at conf.PATH / '.git
    repo = git.Repo.init(path=conf.PATH.absolute(), initial_branch=MAIN_BRANCH_NAME)
    # note that at this point we are assuming the directory is not empty
    commit(INITIAL_COMMIT_MESSAGE)


def commit(message: str, automated: bool = True) -> None:
    """
    Commit all changes to the current project with the given message.
    Include AUTOMATION_NOTE in the commit message if `automated` is `True`.
    """
    try:
        repo = _get_repo()
    except EnvironmentError as e:
        log.warning(e)
        return

    changed_files = get_uncommitted_files()
    if len(changed_files):
        log.debug(f"Committing {len(changed_files)} changed files to {repo.git_dir}")
        repo.index.add(changed_files)
        repo.index.commit(message + (AUTOMATION_NOTE if automated else ''))
        return

    log.debug(f"No changes to commit to {repo.git_dir}")


def get_uncommitted_files() -> list[str]:
    """
    Get a list of all files that have been modified but not committed.
    """
    try:
        repo = _get_repo()
    except EnvironmentError as e:
        log.warning(e)
        return []

    untracked = repo.untracked_files
    modified = [item.a_path for item in repo.index.diff(None)]
    return untracked + modified
