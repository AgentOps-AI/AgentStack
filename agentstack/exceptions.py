class ValidationError(Exception):
    """
    Raised when a validation error occurs ie. a file does not meet the required
    format or a syntax error is found.
    """

    pass

class ToolError(ValidationError):
    """
    Base exception for all tool-related errors. Inherits from ValidationError to maintain
    consistent error handling across the application. All tool-specific exceptions
    should inherit from this class.
    """
    pass
