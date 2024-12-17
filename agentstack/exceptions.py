"""
AgentStack exception classes.
"""


class ValidationError(Exception):
    """
    Raised when a validation error occurs ie. a file does not meet the required
    format or a syntax error is found.
    """

    pass


class AgentProtocolError(ValidationError):
    """Base exception for agent-protocol errors."""

    pass


class ThreadError(AgentProtocolError):
    """Errors related to thread operations in agent-protocol."""

    pass


class RunError(AgentProtocolError):
    """Errors related to run operations in agent-protocol."""

    pass


class StoreError(AgentProtocolError):
    """Errors related to store operations in agent-protocol."""

    pass
