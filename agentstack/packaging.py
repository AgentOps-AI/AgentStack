import os
from typing import Optional

PACKAGING_CMD = "poetry"

def install(package: str, path: Optional[str] = None):
    if path:
        os.chdir(path)
    os.system(f"{PACKAGING_CMD} add {package}")

def remove(package: str):
    os.system(f"{PACKAGING_CMD} remove {package}")

def upgrade(package: str):
    os.system(f"{PACKAGING_CMD} add {package}")
