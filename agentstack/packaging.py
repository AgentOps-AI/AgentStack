import os, sys

PACKAGING_CMD = "poetry"

def install(package: str):
    os.system(f"{PACKAGING_CMD} add {package}")

def remove(package: str):
    os.system(f"{PACKAGING_CMD} remove {package}")

def upgrade(package: str):
    os.system(f"{PACKAGING_CMD} update {package}")

