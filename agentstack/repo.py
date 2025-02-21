from typing import Optional
from types import ModuleType
from pathlib import Path
import shutil
from agentstack import conf, log
from agentstack.exceptions import EnvironmentError

MAIN_BRANCH_NAME = "main"

AUTOMATION_NOTE = "\n\n(This commit was made automatically by AgentStack)"
INITIAL_COMMIT_MESSAGE = "Initial commit."
USER_CHANGES_COMMIT_MESSAGE = "Adding user changes before modifying project."

_USE_GIT = None  # global state to disable git for this run


# The python git module prints an excessive error message when git is not 
# installed. We always want to allow git support to fail silently.
try:
    import git
except ImportError:
    _USE_GIT = False


def should_track_changes() -> bool:
    """
    If git has been disabled for this run, return False. Next, look for the value 
    defined in agentstack.json. Finally, default to True.
    """
    global _USE_GIT

    if _USE_GIT is not None:
        return _USE_GIT

    try:
        return conf.ConfigFile().use_git is not False
    except FileNotFoundError:
        return True


def dont_track_changes() -> None:
    """
    Disable git tracking for one run.
    """
    global _USE_GIT

    _USE_GIT = False


class TrackingDisabledError(EnvironmentError):
    """
    Raised when git is disabled for this run.
    Subclasses `EnvironmentError` so we can early exit using the same logic.
    """

    pass


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
        commit_all_changes(', '.join(self.messages), automated=self.automated)
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
    Raise an EnvironmentError if git is not installed, raise a TrackingDisabledError
    if git tracking is disabled.
    """
    if not should_track_changes():
        raise TrackingDisabledError("Git tracking is disabled by the user.")

    try:
        assert shutil.which('git')
    except AssertionError:
        message = "git is not installed.\nInstall it to track changes to files in your project."
        if shutil.which('apt'):
            message += "\nHint: run `sudo apt install git`"
        elif shutil.which('brew'):
            message += "\nHint: run `brew install git`"
        elif shutil.which('port'):
            message += "\nHint: run `sudo port install git`"
        log.warning(message)  # log now since this won't bubble to the user
        raise EnvironmentError(message)


def find_parent_repo(path: Path) -> Optional[Path]:
    """
    Traverse the directory tree upwards from `path` until a .git directory is found.
    """
    current = path.absolute()
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    return None


def _get_repo() -> git.Repo:
    """
    Get the git repository for the current project.
    Raises:
     - `TrackingDisabledError` if git tracking is disabled.
     - `EnvironmentError` if git is not installed.
     - `EnvironmentError` if the repo is not found.
    """
    _require_git()
    try:
        # look for a repository in the project's directory
        return git.Repo(conf.PATH.absolute())
    except git.exc.InvalidGitRepositoryError:
        message = "No git repository found in the current project."
        log.warning(message)  # log now since this won't bubble to the user
        raise EnvironmentError(message)


def init(force_creation: bool = False) -> None:
    """
    Create a git repository for the current project and commit a .gitignore file
    to initialize the repo. 
    
    `force_creation` will create a new repo even if one already exists in a parent
    directory. default: False
    """
    try:
        _require_git()
    except EnvironmentError as e:
        return  # git is not installed or tracking is disabled
    
    if find_parent_repo(conf.PATH.absolute()):
        log.warning("A git repository already exists in a parent directory.")
        if not force_creation:
            return

    # creates a new repo at conf.PATH / '.git
    repo = git.Repo.init(path=conf.PATH.absolute(), initial_branch=MAIN_BRANCH_NAME)

    # commit gitignore first so we don't add untracked files
    gitignore = conf.PATH.absolute() / '.gitignore'
    gitignore.touch()

    commit(INITIAL_COMMIT_MESSAGE, [str(gitignore)], automated=True)


def commit(message: str, files: list[str], automated: bool = True) -> None:
    """
    Commit the given files to the current project with the given message.
    Include AUTOMATION_NOTE in the commit message if `automated` is `True`.
    """
    try:
        repo = _get_repo()
    except EnvironmentError as e:
        return  # git is not installed or tracking is disabled

    log.debug(f"Committing {len(files)} changed files")
    repo.index.add(files)
    repo.index.commit(message + (AUTOMATION_NOTE if automated else ''))


def commit_all_changes(message: str, automated: bool = True) -> None:
    """
    Commit all changes to the current project with the given message.
    Include AUTOMATION_NOTE in the commit message if `automated` is `True`.
    """
    changed_files = get_uncommitted_files()
    if len(changed_files):
        return commit(message, changed_files, automated=automated)


def commit_user_changes(automated: bool = True) -> None:
    """
    Commit any changes to the current repo as user changes.
    Include AUTOMATION_NOTE in the commit message if `automated` is `True`.
    """
    commit_all_changes(USER_CHANGES_COMMIT_MESSAGE, automated=automated)


def get_uncommitted_files() -> list[str]:
    """
    Get a list of all files that have been modified since the last commit.
    """
    try:
        repo = _get_repo()
    except EnvironmentError as e:
        return []  # git is not installed or tracking is disabled

    untracked = repo.untracked_files
    modified = [item.a_path for item in repo.index.diff(None) if item.a_path]
    return untracked + modified


def revert_last_commit(hard: bool = False) -> None:
    """
    Revert the last commit in the current project.
    """
    try:
        repo = _get_repo()
    except EnvironmentError as e:
        return  # git is not installed or tracking is disabled

    if len(repo.head.commit.parents) == 0:
        log.error("No commits to revert.")
        return

    def _format_commit_message(commit):
        return commit.message.split('\n')[0]

    log.info(f"Reverting: {_format_commit_message(repo.head.commit)}")
    repo.git.reset('HEAD~1', hard=hard)
    log.info(f"Head is now at: {_format_commit_message(repo.head.commit)}")
