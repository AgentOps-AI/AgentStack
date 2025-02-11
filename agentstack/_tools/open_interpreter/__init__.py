import os
from agentstack import tools
from interpreter import interpreter


# 1. Configuration and Tools
interpreter.auto_run = True
interpreter.llm.model = os.getenv("OPEN_INTERPRETER_LLM_MODEL")


def execute_code(code: str):
    """A tool to execute code using Open Interpreter. Returns the output of the code."""
    permissions = tools.get_permissions(execute_code)
    if not permissions.EXECUTE:
        return "User has not granted execute permission."
    
    result = interpreter.chat(f"execute this code with no changes: {code}")
    return result
