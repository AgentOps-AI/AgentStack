import os

def compile_llms_txt():
    # Get the docs directory path (where this script is located)
    docs_dir = os.path.dirname(os.path.abspath(__file__))
    content = ''
    # Define names of directories and files to exclude
    excluded_names = {'tool'}
    
    # Change to docs directory
    os.chdir(docs_dir)
    
    for root, _, files in os.walk('.'):
        # Get the last part of the current directory
        current_dir = os.path.basename(root)
        if current_dir in excluded_names:
            continue
            
        for file in files:
            if file.endswith('.mdx'):
                if file in excluded_names:
                    continue
                    
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, '.')
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                content += f"## {relative_path}\n\n{file_content}\n\n"

    # Write the complete content, replacing the existing file
    output_path = os.path.join(docs_dir, 'llms.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    compile_llms_txt()
