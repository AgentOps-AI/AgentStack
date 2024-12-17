import os, sys
import subprocess

def run_cli(cli_entry, *args):
    """Helper method to run the CLI with arguments. Cross-platform."""
    try:
        # Use shell=True on Windows to handle path issues
        if sys.platform == 'win32':
            # Add PYTHONIOENCODING to the environment
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            result = subprocess.run(
                " ".join(str(arg) for arg in cli_entry + list(args)),
                capture_output=True,
                text=True,
                shell=True,
                env=env,
                encoding='utf-8'
            )
        else:
            result = subprocess.run(
                [*cli_entry, *args],
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