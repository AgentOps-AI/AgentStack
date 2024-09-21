import inquirer
import os


def ask_project_details():
    questions = [
        inquirer.Text('name', message="What's the name of your project"),
        inquirer.Text('version', message="What's the initial version", default="0.1.0"),
        inquirer.Text('description', message="Enter a description for your project"),
        inquirer.Text('author', message="What's your name"),
        inquirer.Text('license', message="License (e.g. MIT, Apache, GPL)", default="MIT"),
    ]

    answers = inquirer.prompt(questions)
    return answers


def ask_package_manager():
    package_managers = [
        'Poetry',
        'Pipenv',
        'Conda',
        'Virtualenv',
        'Other'
    ]

    question = [
        inquirer.List('manager',
                      message="Select your preferred package manager",
                      choices=package_managers,
                      ),
    ]

    answer = inquirer.prompt(question)
    return answer['manager']


def ask_dependencies():
    add_dependencies = inquirer.Confirm('add_deps', message="Do you want to add any dependencies now?", default=True)
    deps_answer = inquirer.prompt([add_dependencies])

    dependencies = []
    if deps_answer['add_deps']:
        while True:
            dep = inquirer.Text('dependency', message="Enter dependency (or leave blank to finish)")
            dep_answer = inquirer.prompt([dep])
            if dep_answer['dependency'] == '':
                break
            dependencies.append(dep_answer['dependency'])

    return dependencies


def create_project(answers, manager, dependencies):
    # Create project folder structure
    os.makedirs(answers['name'], exist_ok=True)
    with open(f"{answers['name']}/pyproject.toml", "w") as f:
        f.write(f"""
[tool.poetry]
name = "{answers['name']}"
version = "{answers['version']}"
description = "{answers['description']}"
authors = ["{answers['author']}"]
license = "{answers['license']}"

[tool.poetry.dependencies]
python = "^3.8"
""")
        for dep in dependencies:
            f.write(f"{dep} = \"*\"\n")

    print(f"Project {answers['name']} created with {manager}!")


def main():
    print("Welcome to the project initializer!")
    project_details = ask_project_details()
    package_manager = ask_package_manager()
    dependencies = ask_dependencies()

    create_project(project_details, package_manager, dependencies)
    print("\nAll done! Happy coding!")


if __name__ == "__main__":
    main()
