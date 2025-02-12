from typing import Optional
from agentstack import conf, log
from agentstack import inputs
from agentstack import run


def run_project(command: str = 'run', cli_args: Optional[list[str]] = None):
    """Validate that the project is ready to run and then run it."""
    run.preflight()

    # Parse extra --input-* arguments for runtime overrides of the project's inputs
    if cli_args:
        for arg in cli_args:
            if not arg.startswith('--input-'):
                continue
            key, value = arg[len('--input-') :].split('=')
            log.debug(f"Using CLI input override: {key}={value}")
            inputs.add_input_for_run(key, value)

    run.run_project(command=command)

