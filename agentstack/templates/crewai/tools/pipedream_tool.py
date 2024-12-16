from crewai_tools import BaseTool
from typing import Optional, Dict
import os
import requests
import json
from pydantic import Field

class PipedreamActionTool(BaseTool):
    name: str = "pipedream_action"
    description: str = "Execute Pipedream component actions"
    base_url: str = "https://api.pipedream.com/v1"
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("PIPEDREAM_API_KEY"))
    headers: Dict[str, str] = Field(default_factory=lambda: {
        "Authorization": f"Bearer {os.getenv('PIPEDREAM_API_KEY')}",
        "Content-Type": "application/json"
    })

    def _run(self, component_id: str, input_data: Optional[dict] = None) -> str:
        try:
            url = f"{self.base_url}/components/{component_id}/event"
            response = requests.post(
                url,
                headers=self.headers,
                json=input_data or {}
            )
            response.raise_for_status()
            return json.dumps(response.json(), indent=2)
        except Exception as e:
            return f"Error executing Pipedream component: {str(e)}"

class PipedreamTriggerTool(BaseTool):
    name: str = "pipedream_trigger"
    description: str = "List Pipedream component events"
    base_url: str = "https://api.pipedream.com/v1"
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("PIPEDREAM_API_KEY"))
    headers: Dict[str, str] = Field(default_factory=lambda: {
        "Authorization": f"Bearer {os.getenv('PIPEDREAM_API_KEY')}",
        "Content-Type": "application/json"
    })

    def _run(self, component_id: str) -> str:
        try:
            url = f"{self.base_url}/components/{component_id}/events"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return json.dumps(response.json(), indent=2)
        except Exception as e:
            return f"Error listing Pipedream events: {str(e)}"

pipedream_action = PipedreamActionTool()
pipedream_trigger = PipedreamTriggerTool()
