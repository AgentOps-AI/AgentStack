import os, sys
import subprocess

CLI_ENTRY = [
    sys.executable,
    "-m",
    "agentstack.main",
]

def run_cli(*args):
    """Helper method to run the CLI with arguments. Cross-platform."""
    try:
        # Use shell=True on Windows to handle path issues
        if sys.platform == 'win32':
            # Add PYTHONIOENCODING to the environment
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            result = subprocess.run(
                " ".join(str(arg) for arg in CLI_ENTRY + list(args)),
                capture_output=True,
                text=True,
                shell=True,
                env=env,
                encoding='utf-8'
            )
        else:
            result = subprocess.run(
                [*CLI_ENTRY, *args],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
        
        if result.returncode != 0:
            print(f"Command failed with code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            
        return result
    except Exception as e:
        print(f"Exception running command: {e}")
        raise