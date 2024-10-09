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
