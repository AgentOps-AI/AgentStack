import os
import httpx

from typing import Optional

QUERY_DATA_ENDPOINT = "https://api.agentql.com/v1/query-data"
API_TIMEOUT_SECONDS = 900

API_KEY = os.getenv("AGENTQL_API_KEY")


def extract_data(
    url: str,
    query: Optional[str],
    prompt: Optional[str],
    is_stealth_mode_enabled: bool = False,
) -> dict:
    """
    url: url of website to scrape
    query: described below
    prompt: Natural language description of the data you want to scrape
    is_stealth_mode_enabled: Enable stealth mode for web scraping (default: False)

    AgentQL query to scrape the url.

    Here is a guide on AgentQL query syntax:

    Enclose all AgentQL query terms within curly braces `{}`. The following query structure isn't valid because the term "social_media_links" is wrongly enclosed within parenthesis `()`.

    ```
    ( # Should be {
        social_media_links(The icons that lead to Facebook, Snapchat, etc.)[]
    ) # Should be }
    ```

    The following query is also invalid since its missing the curly braces `{}`

    ```
    # should include {
    social_media_links(The icons that lead to Facebook, Snapchat, etc.)[]
    # should include }
    ```

    You can't include new lines in your semantic context. The following query structure isn't valid because the semantic context isn't contained within one line.

    ```
    {
        social_media_links(The icons that lead
            to Facebook, Snapchat, etc.)[]
    }
    ```
    """
    payload = {
        "url": url,
        "query": query,
        "prompt": prompt,
        "metadata": {
            "experimental_stealth_mode_enabled": is_stealth_mode_enabled,
        },
    }

    headers = {
        "X-API-Key": f"{API_KEY}",
        "Content-Type": "application/json",
        "X-TF-Request-Origin": "agentstack",
    }

    try:
        response = httpx.post(
            QUERY_DATA_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

    except httpx.HTTPStatusError as e:
        response = e.response
        if response.status_code in [401, 403]:
            raise ValueError(
                "Please, provide a valid API Key. You can create one at https://dev.agentql.com."
            ) from e
        else:
            try:
                error_json = response.json()
                msg = (
                    error_json["error_info"]
                    if "error_info" in error_json
                    else error_json["detail"]
                )
            except (ValueError, TypeError):
                msg = f"HTTP {e}."
            raise ValueError(msg) from e
    else:
        json = response.json()
        return json["data"]
