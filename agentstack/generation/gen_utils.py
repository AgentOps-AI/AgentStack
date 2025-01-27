from typing import Optional
from enum import Enum
import ast


class InsertionPoint(Enum):
    """
    Enum for specifying where to insert generated code.
    """

    BEGIN = 'begin'
    END = 'end'


def insert_code_after_tag(file_path, tag, code_to_insert, next_line=False):
    if next_line:
        code_to_insert = ['\n'] + code_to_insert

    with open(file_path, 'r') as file:
        lines = file.readlines()

    for index, line in enumerate(lines):
        if tag in line:
            # Insert the code block after the tag
            indented_code = [
                (line[: len(line) - len(line.lstrip())] + code_line + '\n') for code_line in code_to_insert
            ]
            lines[index + 1 : index + 1] = indented_code
            break
    else:
        raise ValueError(f"Tag '{tag}' not found in the file.")

    with open(file_path, 'w') as file:
        file.writelines(lines)


def insert_after_tasks(file_path, code_to_insert):
    with open(file_path, 'r') as file:
        content = file.read()

    module = ast.parse(content)

    # Track the last task function and its line number
    last_task_end = None
    last_task_start = None
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef) and any(
            isinstance(deco, ast.Name) and deco.id == 'task' for deco in node.decorator_list
        ):
            last_task_end = node.end_lineno
            last_task_start = node.lineno

    if last_task_end is not None:
        lines = content.split('\n')

        # Get the indentation of the task function
        task_line = lines[last_task_start - 1]  # -1 for 0-based indexing
        indentation = ''
        for char in task_line:
            if char in [' ', '\t']:
                indentation += char
            else:
                break

        # Add the same indentation to each line of the inserted code
        indented_code = '\n' + '\n'.join(indentation + line for line in code_to_insert)

        lines.insert(last_task_end, indented_code)
        content = '\n'.join(lines)

        with open(file_path, 'w') as file:
            file.write(content)
        return True
    else:
        insert_code_after_tag(file_path, '# Task definitions', code_to_insert)


def string_in_file(file_path: str, str_to_match: str) -> bool:
    with open(file_path, 'r') as file:
        file_content = file.read()
        return str_to_match in file_content


def parse_insertion_point(position: Optional[str] = None) -> Optional[InsertionPoint]:
    """
    Parse an insertion point CLI argument into an InsertionPoint enum.
    """
    if position is None:
        return None  # defer assumptions

    valid_positions = {x.value for x in InsertionPoint}
    if position not in valid_positions:
        raise ValueError(f"Position must be one of {','.join(valid_positions)}.")

    return next(x for x in InsertionPoint if x.value == position)
