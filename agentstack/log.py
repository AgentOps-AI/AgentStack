"""
`agentstack.log`

DEBUG:    Detailed technical information, typically of interest when diagnosing problems.
TOOL_USE: A message to indicate the use of a tool.
THINKING: Information about an internal monologue or reasoning.
INFO:     Useful information about the state of the application.
NOTIFY:   A notification or update.
SUCCESS:  An indication of a successful operation.
RESPONSE: A response to a request.
WARNING:  An indication that something unexpected happened, but not severe.
ERROR:    An indication that something went wrong, and the application may not be able to continue.

TODO when running commands outside of a project directory, the log file
is created in the current working directory.
State changes, like going from a pre-initialized project to a valid project,
should trigger a re-initialization of the logger.

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
    'tool_use',
    'thinking',
    'info',
    'notify',
    'success',
    'response',
    'warning',
    'error',
]

LOG_NAME: str = 'agentstack'
LOG_FILENAME: str = 'agentstack.log'

# define additional log levels to accommodate other messages inside the app
DEBUG = logging.DEBUG  # 10
TOOL_USE = 16
THINKING = 18
INFO = logging.INFO  # 20
NOTIFY = 22
SUCCESS = 24
RESPONSE = 26
WARNING = logging.WARNING  # 30
ERROR = logging.ERROR  # 40

logging.addLevelName(THINKING, 'THINKING')
logging.addLevelName(TOOL_USE, 'TOOL_USE')
logging.addLevelName(NOTIFY, 'NOTIFY')
logging.addLevelName(SUCCESS, 'SUCCESS')
logging.addLevelName(RESPONSE, 'RESPONSE')

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
    """Get the logging handler for the given log level."""

    def handler(msg, *args, **kwargs):
        global instance
        if instance is None:
            instance = _build_logger()
        return instance.log(levelno, msg, *args, **kwargs)

    return handler


debug = _create_handler(DEBUG)
tool_use = _create_handler(TOOL_USE)
thinking = _create_handler(THINKING)
info = _create_handler(INFO)
notify = _create_handler(NOTIFY)
success = _create_handler(SUCCESS)
response = _create_handler(RESPONSE)
warning = _create_handler(WARNING)
error = _create_handler(ERROR)


class ConsoleFormatter(logging.Formatter):
    """Formats log messages for display in the console."""

    default_format = logging.Formatter('%(message)s')
    formats = {
        DEBUG: logging.Formatter('DEBUG: %(message)s'),
        SUCCESS: logging.Formatter(term_color('%(message)s', 'green')),
        NOTIFY: logging.Formatter(term_color('%(message)s', 'blue')),
        WARNING: logging.Formatter(term_color('%(message)s', 'yellow')),
        ERROR: logging.Formatter(term_color('%(message)s', 'red')),
    }

    def format(self, record: logging.LogRecord) -> str:
        template = self.formats.get(record.levelno, self.default_format)
        return template.format(record)


class FileFormatter(logging.Formatter):
    """Formats log messages for display in a log file."""

    default_format = logging.Formatter('%(levelname)s: %(message)s')
    formats = {
        DEBUG: logging.Formatter('DEBUG (%(asctime)s):\n %(pathname)s:%(lineno)d\n %(message)s'),
    }

    def format(self, record: logging.LogRecord) -> str:
        template = self.formats.get(record.levelno, self.default_format)
        return template.format(record)


def _build_logger() -> logging.Logger:
    """
    Build the logger with the appropriate handlers.
    All log messages are written to the log file.
    Errors and above are written to stderr if a stream has been configured.
    Warnings and below are written to stdout if a stream has been configured.
    """
    # global stdout, stderr

    log = logging.getLogger(LOG_NAME)
    log.handlers.clear()  # remove any existing handlers
    log.propagate = False  # prevent inheritance from the root logger
    # min log level set here cascades to all handlers
    log.setLevel(DEBUG if conf.DEBUG else INFO)

    try:
        # `conf.PATH` can change during startup, so defer building the path
        log_filename = conf.PATH / LOG_FILENAME

        # log file only gets written to if it exists, which happens on project init
        # this prevents us from littering log files outside of project directories
        if not log_filename.exists():
            raise FileNotFoundError

        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(FileFormatter())
        file_handler.setLevel(DEBUG)
        log.addHandler(file_handler)
    except FileNotFoundError:
        pass  # we are not in a writeable directory

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
