from interpreter import interpreter


# 1. Configuration and Tools
interpreter.auto_run = True
interpreter.llm.model = "gpt-4o"


def execute_code(code: str):
    """A tool to execute code using Open Interpreter. Returns the output of the code."""
    result = interpreter.chat(f"execute this code with no changes: {code}")
    return result
