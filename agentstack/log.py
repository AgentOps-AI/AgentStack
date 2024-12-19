"""
`agentstack.log`

TODO would be cool to intercept all messages from the framework and redirect
them through this logger. This would allow us to capture all messages and display
them in the console and filter based on priority.

TODO With agentstack serve, we can direct all messages to the API, too.
"""

from typing import IO, Optional, Callable
import os, sys
import io
import logging
from agentstack import conf
from agentstack.utils import term_color

__all__ = [
    'set_stdout',
    'set_stderr',
    'debug',
    'success',
    'notify',
    'info',
    'warning',
    'error',
]

LOG_NAME: str = 'agentstack'
LOG_FILENAME: str = 'agentstack.log'

# define additional log levels to accommodate other messages inside the app
# TODO add agent output definitions for messages from the agent
DEBUG = logging.DEBUG  # 10
SUCCESS = 18
NOTIFY = 19
INFO = logging.INFO  # 20
WARNING = logging.WARNING  # 30
ERROR = logging.ERROR  # 40

logging.addLevelName(NOTIFY, 'NOTIFY')
logging.addLevelName(SUCCESS, 'SUCCESS')

# `instance` is lazy so we have time to set up handlers
instance: Optional[logging.Logger] = None

stdout: IO = io.StringIO()
stderr: IO = io.StringIO()


def set_stdout(stream: IO):
    """
    Redirect standard output messages to the given stream.
    In practice, if a shell is available, pass: `sys.stdout`.
    But, this can be any stream that implements the `write` method.
    """
    global stdout, instance
    stdout = stream
    instance = None  # force re-initialization


def set_stderr(stream: IO):
    """
    Redirect standard error messages to the given stream.
    In practice, if a shell is available, pass: `sys.stderr`.
    But, this can be any stream that implements the `write` method.
    """
    global stderr, instance
    stderr = stream
    instance = None  # force re-initialization


def _create_handler(levelno: int) -> Callable:
    """
    Get the logging function for the given log level.
    ie. log.debug("message")
    """

    def handler(msg, *args, **kwargs):
        global instance
        if instance is None:
            instance = _build_logger()
        return instance.log(levelno, msg, *args, **kwargs)

    return handler


debug = _create_handler(DEBUG)
success = _create_handler(SUCCESS)
notify = _create_handler(NOTIFY)
info = _create_handler(INFO)
warning = _create_handler(WARNING)
error = _create_handler(ERROR)


class ConsoleFormatter(logging.Formatter):
    """Formats log messages for display in the console."""

    formats = {
        DEBUG: logging.Formatter('DEBUG: %(message)s'),
        SUCCESS: logging.Formatter(term_color('%(message)s', 'green')),
        NOTIFY: logging.Formatter(term_color('%(message)s', 'blue')),
        INFO: logging.Formatter('%(message)s'),
        WARNING: logging.Formatter(term_color('%(message)s', 'yellow')),
        ERROR: logging.Formatter(term_color('%(message)s', 'red')),
    }

    def format(self, record: logging.LogRecord) -> str:
        return self.formats[record.levelno].format(record)


class FileFormatter(logging.Formatter):
    """Formats log messages for display in a log file."""

    formats = {
        DEBUG: logging.Formatter('DEBUG (%(asctime)s):\n %(pathname)s:%(lineno)d\n %(message)s'),
        SUCCESS: logging.Formatter('%(message)s'),
        NOTIFY: logging.Formatter('%(message)s'),
        INFO: logging.Formatter('INFO: %(message)s'),
        WARNING: logging.Formatter('WARN: %(message)s'),
        ERROR: logging.Formatter('ERROR (%(asctime)s):\n %(pathname)s:%(lineno)d\n %(message)s'),
    }

    def format(self, record: logging.LogRecord) -> str:
        return self.formats[record.levelno].format(record)


def _build_logger() -> logging.Logger:
    """
    Build the logger with the appropriate handlers.
    All log messages are written to the log file.
    Errors and above are written to stderr if a stream has been configured.
    Warnings and below are written to stdout if a stream has been configured.
    """
    # global stdout, stderr

    # `conf.PATH`` can change during startup, so defer building the path
    log_filename = conf.PATH / LOG_FILENAME
    if not os.path.exists(log_filename):
        os.makedirs(log_filename.parent, exist_ok=True)
        log_filename.touch()

    log = logging.getLogger(LOG_NAME)
    # min log level set here cascades to all handlers
    log.setLevel(DEBUG if conf.DEBUG else INFO)

    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(FileFormatter())
    file_handler.setLevel(DEBUG)
    log.addHandler(file_handler)

    # stdout handler for warnings and below
    # `stdout` can change, so defer building the stream until we need it
    stdout_handler = logging.StreamHandler(stdout)
    stdout_handler.setFormatter(ConsoleFormatter())
    stdout_handler.setLevel(DEBUG)
    stdout_handler.addFilter(lambda record: record.levelno < ERROR)
    log.addHandler(stdout_handler)

    # stderr handler for errors and above
    # `stderr` can change, so defer building the stream until we need it
    stderr_handler = logging.StreamHandler(stderr)
    stderr_handler.setFormatter(ConsoleFormatter())
    stderr_handler.setLevel(ERROR)
    log.addHandler(stderr_handler)

    return log
