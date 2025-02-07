# app.py
import importlib
import sys
from pathlib import Path
from dotenv import load_dotenv
from agentstack import conf, frameworks, inputs
from agentstack.exceptions import ValidationError
from agentstack.utils import verify_agentstack_project
# TODO: move this to not cli, but cant be utils due to circular import
from agentstack.cli.run import format_friendly_error_message
from build.lib.agentstack.logger import log

load_dotenv(dotenv_path="/app/.env")

from flask import Flask, request, jsonify
import requests
from typing import Dict, Any, Optional
import os

MAIN_FILENAME: Path = Path("src/main.py")
MAIN_MODULE_NAME = "main"

app = Flask(__name__)


def call_webhook(webhook_url: str, data: Dict[str, Any]) -> None:
    """Send results to the specified webhook URL."""
    try:
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Webhook call failed: {str(e)}")
        raise


@app.route("/health", methods=["GET"])
def health():
    return "Agent Server Up"


@app.route('/process', methods=['POST'])
def process_agent():
    try:
        # Extract data and webhook URL from request
        request_data = request.get_json()
        if not request_data or 'webhook_url' not in request_data:
            return jsonify({'error': 'Missing webhook_url in request'}), 400

        if not request_data or 'inputs' not in request_data:
            return jsonify({'error': 'Missing input data in request'}), 400

        webhook_url = request_data.pop('webhook_url')

        # Run the agent process with the provided data
        # result = WebresearcherCrew().crew().kickoff(inputs=request_data)
        # inputs = json.stringify(request_data)
        # os.system(f"python src/main.py {inputs}")
        result = run_project(api_inputs=request_data.get('inputs'))

        # Call the webhook with the results
        call_webhook(webhook_url, {
            'status': 'success',
            'result': result
        })

        return jsonify({
            'status': 'success',
            'message': 'Agent process completed and webhook called'
        })

    except Exception as e:
        error_message = str(e)
        app.logger.error(f"Error processing request: {error_message}")

        # Attempt to call webhook with error information
        if webhook_url:
            try:
                call_webhook(webhook_url, {
                    'status': 'error',
                    'error': error_message
                })
            except:
                pass  # Webhook call failed, but we still want to return the error to the caller

        return jsonify({
            'status': 'error',
            'error': error_message
        }), 500


def run_project(command: str = 'run', api_args: Optional[Dict[str, str]] = None,
                api_inputs: Optional[Dict[str, str]] = None):
    """Validate that the project is ready to run and then run it."""
    verify_agentstack_project()

    if conf.get_framework() not in frameworks.SUPPORTED_FRAMEWORKS:
        raise ValidationError(f"Framework {conf.get_framework()} is not supported by agentstack.")

    try:
        frameworks.validate_project()
    except ValidationError as e:
        raise e

    for key, value in api_inputs.items():
        inputs.add_input_for_run(key, value)

    load_dotenv(Path.home() / '.env')  # load the user's .env file
    load_dotenv(conf.PATH / '.env', override=True)  # load the project's .env file

    # import src/main.py from the project path and run `command` from the project's main.py
    try:
        log.notify("Running your agent...")
        project_main = _import_project_module(conf.PATH)
        getattr(project_main, command)()
    except ImportError as e:
        raise ValidationError(f"Failed to import AgentStack project at: {conf.PATH.absolute()}\n{e}")
    except Exception as e:
        raise Exception(format_friendly_error_message(e))

def _import_project_module(path: Path):
    """
    Import `main` from the project path.

    We do it this way instead of spawning a subprocess so that we can share
    state with the user's project.
    """
    spec = importlib.util.spec_from_file_location(MAIN_MODULE_NAME, str(path / MAIN_FILENAME))

    assert spec is not None  # appease type checker
    assert spec.loader is not None  # appease type checker

    project_module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str((path / MAIN_FILENAME).parent))
    spec.loader.exec_module(project_module)
    return project_module


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 6969))

    print("🚧 Running your agent on a development server")
    print(f"Send agent requests to http://localhost:{port}")
    print("Learn more about agent requests at https://docs.agentstack.sh/") # TODO: add docs for this

    app.run(host='0.0.0.0', port=port)