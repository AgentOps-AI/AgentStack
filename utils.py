import toml


def get_version():
    try:
        with open('pyproject.toml', 'r') as f:
            pyproject_data = toml.load(f)
            return pyproject_data['tool']['poetry']['version']
    except (KeyError, FileNotFoundError):
        return "Unknown version"

