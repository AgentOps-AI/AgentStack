import os
from pathlib import Path
from agentstack.cli.cli import init_project_builder
from agentstack import conf

def setup_agentstack_project():
    project_name = "agent_web_interface"
    project_dir = Path(os.getcwd()).parent.parent / project_name

    # Initialize the project
    if not project_dir.exists():
        init_project_builder(project_name)
        print(f"Created AgentStack project at {project_dir}")
    else:
        print(f"Project directory already exists at {project_dir}")
        conf.set_path(str(project_dir))

    return project_dir

if __name__ == "__main__":
    setup_agentstack_project()
