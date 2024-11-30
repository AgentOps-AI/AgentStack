import os, sys

PACKAGING_CMD = "poetry"

def install(package: str):
    os.system(f"{PACKAGING_CMD} add {package}")

def remove(package: str):
    os.system(f"{PACKAGING_CMD} remove {package}")

def upgrade(package: str):
    packages = package.split(' ')
    packages_latest = ' '.join(f"{pkg}@latest" for pkg in packages)
    os.system(f"{PACKAGING_CMD} add {packages_latest}")

