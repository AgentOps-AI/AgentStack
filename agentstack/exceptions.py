class ValidationError(Exception):
    """
    Raised when a validation error occurs ie. a file does not meet the required
    format or a syntax error is found.
    """

    pass

class ToolError(Exception):
    """
    Base exception for all tool-related errors. All exceptions inside of tool
    implementations should inherit from this class.
    """
    pass
