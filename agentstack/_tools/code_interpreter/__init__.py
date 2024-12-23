import os
from agentstack.utils import get_package_path
import docker

CONTAINER_NAME = "code-interpreter"
DEFAULT_IMAGE_TAG = os.getenv("CODE_INTERPRETER_DEFAULT_IMAGE_TAG", "code-interpreter:latest")
DOCKERFILE_PATH = os.getenv("CODE_INTERPRETER_DOCKERFILE_PATH", get_package_path() / "tools/code_interpreter")

client = docker.from_env()


def _verify_docker_image() -> None:
    try:
        client.images.get(DEFAULT_IMAGE_TAG)
    except docker.errors.ImageNotFound:
        if not os.path.exists(DOCKERFILE_PATH):
            raise Exception(
                (
                    "Dockerfile path has not been provided.\n"
                    "Did you set the DOCKERFILE_PATH in you project's .env file?"
                )
            )

        client.images.build(
            path=DOCKERFILE_PATH,
            tag=DEFAULT_IMAGE_TAG,
            rm=True,
        )


def _init_docker_container() -> docker.models.containers.Container:
    current_path = os.getcwd()
    client = docker.from_env()

    # kill container if it's already running
    try:
        existing_container = client.containers.get(CONTAINER_NAME)
        existing_container.stop()
        existing_container.remove()
    except docker.errors.NotFound:
        pass

    return client.containers.run(
        DEFAULT_IMAGE_TAG,
        detach=True,
        tty=True,
        working_dir="/workspace",
        name=CONTAINER_NAME,
        volumes={current_path: {"bind": "/workspace", "mode": "rw"}},  # type: ignore
    )


def run_code(code: str, libraries_used: list[str]) -> str:
    """
    Run the code in a Docker container using Python 3.

    The container will be built and started, the code will be executed, and the container will be stopped.

    Args:
        code: The code to be executed. ALWAYS PRINT the final result and the output of the code.
        libraries_used: A list of libraries to be installed in the container before running the code.
    """
    _verify_docker_image()
    container = _init_docker_container()

    for library in libraries_used:
        container.exec_run(f"pip install {library}")

    result = container.exec_run(f'python3 -c "{code}"')
    container.stop()
    container.remove()

    return f"exit code: {result.exit_code}\n" f"{result.output.decode('utf-8')}"
