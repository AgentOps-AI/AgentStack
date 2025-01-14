class ValidationError(Exception):
    """
    Raised when a validation error occurs ie. a file does not meet the required
    format or a syntax error is found.
    """

    pass


class EnvironmentError(Exception):
    """
    Raised when an error occurs in the execution environment ie. a command is
    not present or the environment is not configured as expected.
    """

    pass
