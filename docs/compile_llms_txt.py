import os
from pathlib import Path

def compile_llms_txt():
    # Get the current working directory
    current_dir = Path(os.getcwd())
    content = ''
    
    # Define names of directories and files to exclude
    excluded_names = {'tool'}
    
    for root, _, files in os.walk('.'):
        # Get the last part of the current directory
        current_dir = os.path.basename(root)
        if current_dir in excluded_names:
            continue
            
        for file in files:
            # Check if the file is an MDX file and not in excluded names
            if file.endswith('.mdx'):
                # Extract the base name without extension for exclusion check
                base_name = os.path.splitext(file)[0]
                if base_name in excluded_names:
                    continue
                    
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, '.')
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                content += f"## {relative_path}\n\n{file_content}\n\n"

    # Write the complete content to llms.txt in the current directory
    output_path = Path('llms.txt')
    output_path.write_text(content, encoding='utf-8')

if __name__ == "__main__":
    compile_llms_txt()
