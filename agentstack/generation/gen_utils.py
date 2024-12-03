import ast
import sys
from enum import Enum
from typing import Optional, Union, List

from agentstack.utils import term_color


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

    # Track the last task function and its line number
    last_task_end = None
    last_task_start = None
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef) and \
                any(isinstance(deco, ast.Name) and deco.id == 'task' for deco in node.decorator_list):
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


def _framework_filename(framework: str, path: str = ''):
    if framework == 'crewai':
        return f'{path}src/crew.py'

    print(term_color(f'Unknown framework: {framework}', 'red'))
    sys.exit(1)


class CrewComponent(str, Enum):
    AGENT = "agent"
    TASK = "task"


def get_crew_components(
        framework: str = 'crewai',
        component_type: Optional[Union[CrewComponent, List[CrewComponent]]] = None,
        path: str = ''
) -> dict[str, List[str]]:
    """
    Get names of components (agents and/or tasks) defined in a crew file.

    Args:
        framework: Name of the framework
        component_type: Optional filter for specific component types.
                      Can be CrewComponentType.AGENT, CrewComponentType.TASK,
                      or a list of types. If None, returns all components.
        path: Optional path to the framework file

    Returns:
        Dictionary with 'agents' and 'tasks' keys containing lists of names
    """
    filename = _framework_filename(framework, path)

    # Convert single component type to list for consistent handling
    if isinstance(component_type, CrewComponent):
        component_type = [component_type]

    # Read the source file
    with open(filename, 'r') as f:
        source = f.read()

    # Parse the source into an AST
    tree = ast.parse(source)

    components = {
        'agents': [],
        'tasks': []
    }

    # Find all function definitions with relevant decorators
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check decorators
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name):
                    if (component_type is None or CrewComponent.AGENT in component_type) \
                            and decorator.id == 'agent':
                        components['agents'].append(node.name)
                    elif (component_type is None or CrewComponent.TASK in component_type) \
                            and decorator.id == 'task':
                        components['tasks'].append(node.name)

    # If specific types were requested, only return those
    if component_type:
        return {k: v for k, v in components.items()
                if CrewComponent(k[:-1]) in component_type}

    return components
