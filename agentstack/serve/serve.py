from typing import Optional, Any, Callable, Generator
import os, sys
import io
from threading import Thread
import time
import importlib
from enum import Enum
from pathlib import Path
import pydantic
from urllib.parse import urlparse
import json
import requests
from dotenv import load_dotenv

from flask import Flask, send_file, request, jsonify
from flask import Response as BaseResponse
from flask_sock import Sock
from flask_cors import CORS

from agentstack import conf, log
from agentstack.exceptions import ValidationError
from agentstack import inputs
from agentstack import run


load_dotenv(dotenv_path="/app/.env")
#app = Flask(__name__)

#current_webhook_url = None

ALLOWED_ORIGINS = ['*']

class Message(pydantic.BaseModel):
    class Type(str, Enum):
        CHAT = "chat"
    
    type: Type
    data: dict[str, Any]


# TODO subclass flask.Response for response types
class Response(pydantic.BaseModel):
    class Type(str, Enum):
        DATA = "data"
        SUCCESS = "success"
        ERROR = "error"
    
    type: Type
    data: Optional[dict[str, Any]] = None


def call_webhook(webhook_url: str, data: dict[str, Any]) -> None:
    """Send results to the specified webhook URL."""
    try:
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Webhook call failed: {str(e)}")
        raise


# @app.route("/health", methods=["GET"])
# def health():
#     return "Agent Server Up"

# @app.route('/process', methods=['POST'])
# def process_agent():
#     global current_webhook_url

#     request_data = None
#     try:
#         request_data = request.get_json()

#         if not request_data or 'webhook_url' not in request_data:
#             result, message = validate_url(request_data.get("webhook_url"))
#             if not result:
#                 return jsonify({'error': f'Invalid webhook_url in request: {message}'}), 400

#         if not request_data or 'inputs' not in request_data:
#             return jsonify({'error': 'Missing input data in request'}), 400

#         current_webhook_url = request_data.pop('webhook_url')

#         return jsonify({
#             'status': 'accepted',
#             'message': 'Agent process started'
#         }), 202

#     except Exception as e:
#         error_message = str(e)
#         app.logger.error(f"Error processing request: {error_message}")
#         return jsonify({
#             'status': 'error',
#             'error': error_message
#         }), 500

#     finally:
#         if current_webhook_url:
#             try:
#                 result, session_id = run_project(api_inputs=request_data.get('inputs'))
#                 call_webhook(current_webhook_url, {
#                     'status': 'success',
#                     'result': result,
#                     'session_id': session_id
#                 })
#             except Exception as e:
#                 error_message = str(e)
#                 app.logger.error(f"Error in process: {error_message}")
#                 try:
#                     call_webhook(current_webhook_url, {
#                         'status': 'error',
#                         'error': error_message
#                     })
#                 except:
#                     app.logger.error("Failed to send error to webhook")
#             finally:
#                 current_webhook_url = None


def run_project(command: str = 'run', api_args: Optional[dict[str, str]] = None,
                api_inputs: Optional[dict[str, str]] = None):
    """Validate that the project is ready to run and then run it."""
    # TODO `api_args` is unused
    run.preflight()

    for key, value in api_inputs.items():
        inputs.add_input_for_run(key, value)

    run.run_project(command=command)


class GeneratorIO:
    """Behaves like streamIO but is iterable"""
    def __init__(self):
        self.buffer = io.StringIO()
        self._pos = 0
    
    def write(self, text: str) -> int:
        self.buffer.write(text)
        return len(text)
    
    def flush(self) -> None:
        pass

    def __iter__(self) -> Generator[str, None, None]:
        while True:
            self.buffer.seek(self._pos)
            data = self.buffer.read()
            if data:
                self._pos = self.buffer.tell()
                yield data
            else:
                break


def run_project_stream(inputs: dict[str, str], command: str = 'run') -> Generator[str, None, None]:
    """Validate that the project is ready to run and then run it."""
    log_output = GeneratorIO()
    log.set_stream(log_output)

    thread = Thread(target=lambda: run_project(command=command, api_inputs=inputs))
    thread.start()

    while thread.is_alive():
        for line in log_output:
            yield line
        time.sleep(0.1)
    
    for line in log_output:  # stragglers post-thread
        yield line

    thread.join()


def validate_url(url: str) -> tuple[bool, str]:
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


class ProjectServer:
    app: Flask
    sock: Sock
    webhook_url: Optional[str] = None
    
    def __init__(self):
        self.app = Flask(__name__)
        self.sock = Sock(self.app)
        
        CORS(self.app, 
             origins=ALLOWED_ORIGINS,
             methods=["*"])
        self.register_routes()
    
    def register_routes(self):
        """Register all routes for the application"""
        routes = self.get_routes()
        for route, handler, method in routes:
            if method in ('GET', 'POST', 'PUT', 'DELETE'):
                # Regular HTTP routes
                self.app.route(route, methods=[method])(handler)
            else:
                # WebSocket routes
                self.sock.route(route)(handler)
    
    def get_routes(self) -> list[tuple[str, Callable, str]]:
        return [
            ('/', self.index, 'GET'), 
            ('/ws', self.websocket_handler, None), 
            ('/health', self.health, 'GET'), 
            ('/process', self.process, 'POST'),
        ]
    
    def format_response(self, response: Response) -> BaseResponse:
        """Dump a response object to JSON"""
        return jsonify(response.model_dump())
    
    def index(self):
        """Serve a user interface"""
        # TODO delegate this to the user project. 
        return send_file(conf.PATH / 'src/index.html'), 200
    
    def health(self) -> BaseResponse:
        """Health check endpoint"""
        response = Response(
            type=Response.Type.DATA,
            data={'status': 'ok'},
        )
        return self.format_response(response), 200
    
    def process(self) -> BaseResponse:
        request_data = None
        try:
            request_data = request.get_json()

            if not request_data or 'webhook_url' not in request_data:
                result, message = validate_url(request_data.get("webhook_url"))
                if not result:
                    raise ValueError(f'Invalid webhook_url in request: {message}')
            
            if not request_data or 'inputs' not in request_data:
                raise ValueError('Missing input data in request')

            self.webhook_url = request_data.pop('webhook_url')
            return self.format_response(Response(
                type=Response.Type.SUCCESS,
                data={'message': 'Agent process started'}
            )), 202
        
        except Exception as e:
            error_message = str(e)
            # TODO agentstack.log?
            app.logger.error(f"Error processing request: {error_message}")
            return self.format_response(Response(
                type=Response.Type.ERROR,
                data={'message': error_message}
            )), 500

        finally:
            if not self.webhook_url:
                # TODO project will not run if we don't have a webhook url
                # can we just yolo it into the void or should we tell the user first?
                return

            try:
                assert request_data, "request_data is None"
                # TODO `command`
                result, session_id = run_project(api_inputs=request_data.get('inputs'))
                call_webhook(current_webhook_url, {
                    'status': 'success',
                    'result': result,
                    'session_id': session_id
                })
            except Exception as e:
                error_message = str(e)
                # TODO agentstack.log?
                app.logger.error(f"Error in process: {error_message}")
                try:
                    call_webhook(current_webhook_url, {
                        'status': 'error',
                        'error': error_message
                    })
                except:
                    # TODO agentstack.log?
                    app.logger.error("Failed to send error to webhook")
            finally:
                self.webhook_url = None
    
    def handle_message(self, message: Message) -> Generator[Response, None, None]:
        """Handle incoming messages"""
        if message.type == Message.Type.CHAT:
            assert 'role' in message.data
            assert 'content' in message.data
            
            inputs = {
                'prompt': message.data['content'],
            }
            
            # TODO assistant is hardcoded
            for content in run_project_stream(inputs):
                yield Response(
                    type=Response.Type.DATA,
                    data={'role': 'assistant', 'content': content},
                )
                time.sleep(0.01)  # small delay to prevent overwhelming the socket
    
    def get_response(self, message: dict[str, Any]) -> Generator[Response, None, None]:
        """Process incoming message and generate responses"""
        try:
            _message = Message.model_validate(message)
            for response in self.handle_message(_message):
                yield response
        except ValueError as e:
            yield Response(
                type=Response.Type.ERROR,
                data={'error': f"Invalid message format: {str(e)}"},
            )
        except Exception:
            yield Response(
                type=Response.Type.ERROR,
                data={'error': "Unknown message type"},
            )
    
    def websocket_handler(self, ws):
        """Handle WebSocket connections"""
        while True:
            try:
                raw_message = json.loads(ws.receive())
                for response in self.get_response(raw_message):
                    ws.send(json.dumps(response.model_dump()))
            except Exception as e:
                response = Response(
                    type=Response.Type.ERROR,
                    data={'error': str(e)}
                )
                ws.send(json.dumps(response.model_dump()))
                break
    
    def run(self, host='0.0.0.0', port=6969, **kwargs):
        """Run the Flask application"""
        self.app.run(host=host, port=port, **kwargs)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 6969))
    print("🚧 Running your agent on a development server")
    print(f"Send agent requests to http://localhost:{port}")
    print("Learn more about agent requests at https://docs.agentstack.sh/")  # TODO: add docs for this

    log.set_stderr(sys.stderr)
    log.set_stdout(sys.stdout)
    conf.set_path(Path.cwd())
    
    app = ProjectServer()
    app.run(host='0.0.0.0', port=port)
else:
    print("Starting production server with Gunicorn")