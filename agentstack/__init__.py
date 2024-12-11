"""
This it the beginning of the agentstack public API. 

Methods that have been imported into this file are expected to be used by the
end user inside of their project. 
"""
from agentstack.inputs import get_inputs

___all___ = [
    "ValidationError", 
    "get_inputs", 
]

class ValidationError(Exception):
    """
    Raised when a validation error occurs ie. a file does not meet the required
    format or a syntax error is found.
    """
    pass

