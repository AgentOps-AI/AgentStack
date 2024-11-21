import os
import requests

from crewai_tools import tool

from dotenv import load_dotenv
load_dotenv()

url = "https://api.agentql.com/v1/query-data"
api_key = os.getenv("AGENTQL_API_KEY")

@tool
def query_agentql(url: str, query: str):
    """
    Query AgentQL with a query and return the result.
    """

    payload = {
        "url": url,
        "query": query
    }

    headers = {
        "X-API-Key": f"{api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200 and response.text:
        return response.text
    else:
        print(f"{response.status_code} - {response.text}")
        return "Failed to query AgentQL"