import ast


def insert_code_after_tag(file_path, tag, code_to_insert, next_line=False):
    if next_line:
        code_to_insert = ['\n'] + code_to_insert

    with open(file_path, 'r') as file:
        lines = file.readlines()

    for index, line in enumerate(lines):
        if tag in line:
            # Insert the code block after the tag
            indented_code = [(line[:len(line)-len(line.lstrip())] + code_line + '\n') for code_line in code_to_insert]
            lines[index+1:index+1] = indented_code
            break
    else:
        raise ValueError(f"Tag '{tag}' not found in the file.")

    with open(file_path, 'w') as file:
        file.writelines(lines)


def insert_after_tasks(file_path, code_to_insert):
    with open(file_path, 'r') as file:
        content = file.read()

    module = ast.parse(content)

    # Track the last task function's end line
    last_task_end = None
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef) and \
                any(isinstance(deco, ast.Name) and deco.id == 'task' for deco in node.decorator_list):
            last_task_end = node.end_lineno

    if last_task_end is not None:
        lines = content.split('\n')
        for i, line in enumerate(code_to_insert):
            lines.insert(last_task_end + i, line)
        content = '\n'.join(lines)

        with open(file_path, 'w') as file:
            file.write(content)
        return True
    return False

