import importlib
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from agentstack import conf, frameworks, inputs, log
from agentstack.exceptions import ValidationError
from agentstack.utils import verify_agentstack_project
# TODO: move this to not cli, but cant be utils due to circular import
from agentstack.cli.run import format_friendly_error_message
from flask import Flask, request, jsonify
import requests
from typing import Dict, Any, Optional, Tuple
import os

MAIN_FILENAME: Path = Path("src/main.py")
MAIN_MODULE_NAME = "main"

load_dotenv(dotenv_path="/app/.env")
app = Flask(__name__)

current_webhook_url = None

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
    global current_webhook_url

    request_data = None
    try:
        request_data = request.get_json()

        if not request_data or 'webhook_url' not in request_data:
            result, message = validate_url(request_data.get("webhook_url"))
            if not result:
                return jsonify({'error': f'Invalid webhook_url in request: {message}'}), 400

        if not request_data or 'inputs' not in request_data:
            return jsonify({'error': 'Missing input data in request'}), 400

        current_webhook_url = request_data.pop('webhook_url')

        return jsonify({
            'status': 'accepted',
            'message': 'Agent process started'
        }), 202

    except Exception as e:
        error_message = str(e)
        app.logger.error(f"Error processing request: {error_message}")
        return jsonify({
            'status': 'error',
            'error': error_message
        }), 500

    finally:
        if current_webhook_url:
            try:
                result, session_id = run_project(api_inputs=request_data.get('inputs'))
                call_webhook(current_webhook_url, {
                    'status': 'success',
                    'result': result,
                    'session_id': session_id
                })
            except Exception as e:
                error_message = str(e)
                app.logger.error(f"Error in process: {error_message}")
                try:
                    call_webhook(current_webhook_url, {
                        'status': 'error',
                        'error': error_message
                    })
                except:
                    app.logger.error("Failed to send error to webhook")
            finally:
                current_webhook_url = None

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

    try:
        log.notify("Running your agent...")
        project_main = _import_project_module(conf.PATH)
        return getattr(project_main, command)()
    except ImportError as e:
        raise ValidationError(f"Failed to import AgentStack project at: {conf.PATH.absolute()}\n{e}")
    except Exception as e:
        raise Exception(format_friendly_error_message(e))

def _import_project_module(path: Path):
    """Import `main` from the project path."""
    spec = importlib.util.spec_from_file_location(MAIN_MODULE_NAME, str(path / MAIN_FILENAME))

    assert spec is not None
    assert spec.loader is not None

    project_module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str((path / MAIN_FILENAME).parent))
    spec.loader.exec_module(project_module)
    return project_module

def validate_url(url: str) -> Tuple[bool, str]:
    """Validates a URL and returns a tuple of (is_valid, error_message)."""
    if not url:
        return False, "URL cannot be empty"

    try:
        result = urlparse(url)

        if not result.scheme:
            return False, "Missing protocol (e.g., http:// or https://)"

        if not result.netloc:
            return False, "Missing domain name"

        if result.scheme not in ['http', 'https']:
            return False, f"Invalid protocol: {result.scheme}"

        if '.' not in result.netloc:
            return False, "Invalid domain format"

        return True, ""

    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


def get_waitress_config():
    return {
        'host': '0.0.0.0',
        'port': int(os.getenv('PORT') or '6969'),
        'threads': 1,                      # Similar to Gunicorn threads
        'connection_limit': 1,             # Similar to worker_connections
        'channel_timeout': 300,            # Similar to timeout
        'cleanup_interval': 2,             # Similar to keepalive
        'log_socket_errors': True,
        'max_request_body_size': 1073741824,  # 1GB
        'clear_untrusted_proxy_headers': True
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 6969))
    print("🚧 Running your agent on a development server")
    print(f"Send agent requests to http://localhost:{port}")
    print("Learn more about agent requests at https://docs.agentstack.sh/")  # TODO: add docs for this

    app.run(host='0.0.0.0', port=port)
else:
    print("Starting production server with Gunicorn")