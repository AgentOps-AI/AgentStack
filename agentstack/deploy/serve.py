# app.py
from flask import Flask, request, jsonify
import requests
from typing import Dict, Any
import os
from main import run
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

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

        webhook_url = request_data.pop('webhook_url')

        # Run the agent process with the provided data
        # result = WebresearcherCrew().crew().kickoff(inputs=request_data)
        # inputs = json.stringify(request_data)
        # os.system(f"python src/main.py {inputs}")
        result = run(request_data)

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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 6969))
    app.run(host='0.0.0.0', port=port)
