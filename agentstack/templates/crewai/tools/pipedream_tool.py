from typing import Optional, Dict, Any
from crewai_tools import BaseTool
import os
import requests
from json import JSONDecodeError


class PipedreamError(Exception):
    """Custom exception for Pipedream API errors"""
    pass


class PipedreamActionTool(BaseTool):
    name: str = "Pipedream Action"
    description: str = "Execute Pipedream component actions. Requires component_id and input parameters."

    def _execute(self, component_id: str, inputs: Dict[str, Any]) -> str:
        """
        Execute a Pipedream component action.

        Args:
            component_id: The ID of the Pipedream component to execute
            inputs: Dictionary of input parameters for the component

        Returns:
            str: JSON response from the component execution

        Raises:
            PipedreamError: If the API request fails or returns an error
        """
        api_key = os.getenv("PIPEDREAM_API_KEY")
        if not api_key:
            raise PipedreamError("PIPEDREAM_API_KEY environment variable not set")

        try:
            response = requests.post(
                "https://api.pipedream.com/v1/connect/actions/run",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"id": component_id, "configured_props": inputs}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise PipedreamError(f"Failed to execute Pipedream action: {str(e)}")
        except JSONDecodeError:
            raise PipedreamError("Invalid JSON response from Pipedream API")


class PipedreamSourceTool(BaseTool):
    name: str = "Pipedream Source"
    description: str = "Deploy Pipedream component sources. Requires component_id, webhook_url, and configuration parameters."

    def _execute(self, component_id: str, webhook_url: str, config: Dict[str, Any]) -> str:
        """
        Deploy a Pipedream component source.

        Args:
            component_id: The ID of the Pipedream component to deploy
            webhook_url: The URL where events will be sent
            config: Dictionary of configuration parameters for the component

        Returns:
            str: JSON response from the component deployment

        Raises:
            PipedreamError: If the API request fails or returns an error
        """
        api_key = os.getenv("PIPEDREAM_API_KEY")
        if not api_key:
            raise PipedreamError("PIPEDREAM_API_KEY environment variable not set")

        try:
            response = requests.post(
                "https://api.pipedream.com/v1/connect/triggers/deploy",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "id": component_id,
                    "webhook_url": webhook_url,
                    "configured_props": config
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise PipedreamError(f"Failed to deploy Pipedream source: {str(e)}")
        except JSONDecodeError:
            raise PipedreamError("Invalid JSON response from Pipedream API")
