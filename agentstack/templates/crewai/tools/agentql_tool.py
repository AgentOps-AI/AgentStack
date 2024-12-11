import os
import requests

from pydantic import BaseModel, Field
from typing import Optional, Type

from crewai_tools import BaseTool

from dotenv import load_dotenv
load_dotenv()

QUERY_DATA_ENDPOINT = "https://api.agentql.com/v1/query-data"
api_key = os.getenv("AGENTQL_API_KEY")

class AgentQLQueryDataSchema(BaseModel):
    url: str = Field(description="Website URL")
    query: Optional[str] = Field(
        default=None,
        description="""
AgentQL query to scrape the url.

Here is a guide on AgentQL query syntax:

Enclose all AgentQL query terms within curly braces `{}`. The following query structure isn't valid because the term "social\_media\_links" is wrongly enclosed within parenthesis `()`.

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
    )
    prompt: Optional[str] = Field(
        default=None,
        description="Natural language description of the data you want to scrape"
    )

class AgentQLQueryDataTool(BaseTool):
    name: str = "query_data"
    description: str = "Scrape a url with a given AgentQL query or a natural language description of the data you want to scrape."
    args_schema: Type[BaseModel] = AgentQLQueryDataSchema

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _run(
        self,
        url: str,
        query: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> dict:
        payload = {
            "url": url,
            "query": query,
            "prompt": prompt
        }

        headers = {
            "X-API-Key": f"{api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(QUERY_DATA_ENDPOINT, headers=headers, json=payload)
        if response.status_code == 200 and response.text:
            return response.text
        else:
            print(f"{response.status_code} - {response.text}")
            return "Failed to query AgentQL"
        
def createTool(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper()

@createTool
def query_data():
    return AgentQLQueryDataTool()