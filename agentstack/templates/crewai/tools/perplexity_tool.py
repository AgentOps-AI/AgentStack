import os

import requests
from crewai_tools import tool

from dotenv import load_dotenv
load_dotenv()

url = "https://api.perplexity.ai/chat/completions"
api_key = os.getenv("PERPLEXITY_API_KEY")

@tool
def query_perplexity(query: str):
    """
    Use Perplexity to concisely search the internet and answer a query with up-to-date information.
    """

    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        # "max_tokens": "Optional",
        "temperature": 0.2,
        "top_p": 0.9,
        "return_citations": True,
        "search_domain_filter": ["perplexity.ai"],
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": "month",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)
    if response.status_code == 200 and response.text:
        return response.text
    else:
        print(f"{response.status_code} - {response.text}")
        return "Failed to query perplexity"
