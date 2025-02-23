import os, sys
import io
import re
import hashlib
import tempfile
from pathlib import Path
import docker
from docker.errors import DockerException

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PYTHON_VERSIONS: list[str] = [">=3.10,<3.13", "3.10", "3.11", "3.12"]

# make sure your local Docker install has a public socket
# set credstore: "" in ~/.docker/config.json
client = docker.DockerClient(base_url=f'unix://var/run/docker.sock')


def print_green(text: str):
    print(f"\033[92m{text}\033[0m")

def print_red(text: str):
    print(f"\033[91m{text}\033[0m")

def _run_vm(name: str, python_version: str, packages: list[str], command: str) -> str:
    dockerfile = f"""
FROM ubuntu:latest
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y {" ".join(packages)}

WORKDIR /root

COPY install.sh /root/install.sh
RUN chmod +x /root/install.sh
"""
    dockerfile_hash = hashlib.md5(dockerfile.encode("utf-8")).hexdigest()
    install_script_hash = hashlib.md5((BASE_DIR / 'install.sh').read_bytes()).hexdigest()
    hash = hashlib.md5((dockerfile_hash + install_script_hash).encode("utf-8")).hexdigest()
    image_name = F"{re.sub('[<>=,.]', '', python_version)}-{name}-{hash}"

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        script = BASE_DIR / 'install.sh'
        with open(path / 'install.sh', 'wb') as f:
            f.write(script.read_bytes())
        with open(path / 'Dockerfile', 'w') as f:
            f.write(dockerfile)

        image, build_logs = client.images.build(
            tag=image_name, 
            path=tmpdir, 
            rm=True,
        )

    container = client.containers.run(
        image=image, 
        command=command, 
        detach=False, 
    )
    return container.decode("utf-8")


def test_default(python_version: str):
    result = _run_vm(
        test_default.__name__, 
        python_version, 
        ["build-essential", "git", "curl"],
        "bash -c ./install.sh --python-version={python_version}"
    )
    assert "Setup complete!" in result


def test_wget(python_version: str):
    result = _run_vm(
        test_wget.__name__, 
        python_version, 
        ["build-essential", "git", "wget"],
        "bash -c ./install.sh --python-version={python_version}"
    )
    assert "Setup complete!" in result


def test_dev_branch(python_version: str):
    result = _run_vm(
        test_dev_branch.__name__, 
        python_version, 
        ["build-essential", "git", "curl"],
        "bash -c ./install.sh --dev-branch=main --python-version={python_version}"
    )
    assert "Setup complete!" in result


if __name__ == "__main__":
    if "--quick" in sys.argv:
        try:
            print(f"{PYTHON_VERSIONS[0]}:test_default", end="\t")
            test_default(PYTHON_VERSIONS[0])
            print_green(f"PASS")
        except AssertionError:
            print_red(f"FAIL")
        sys.exit(0)
    
    for method in [func for func in dir() if func.startswith("test_")]:
        for version in PYTHON_VERSIONS:
            try:
                print(f"{version}:{method}", end="\t")
                globals()[method](version)
                print_green(f"PASS")
            except AssertionError:
                print_red(f"FAIL")
