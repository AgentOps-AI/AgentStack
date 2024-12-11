import os

from pydantic import BaseModel, Field
from typing import Optional, Type

from crewai_tools import BaseTool

from dotenv import load_dotenv
load_dotenv()

QUERY_DATA_ENDPOINT = "http://0.0.0.0:8080/v1/query-data"
api_key = os.getenv("AGENTQL_API_KEY")

class AgentQLQueryDataSchema(BaseModel):
    url: str = Field(description="Website URL")
    query: Optional[str] = Field(
        default=None,
        description="AgentQL query to scrape the url"
    )
    description: Optional[str] = Field(
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
        description: Optional[str] = None
    ) -> dict:
        if query: 
            return {"data": [{"name": "T-Shirt", "price": 100}, {"name": "Pants", "price": 200}]}
        elif description:
            return {"data": [{"name": "Coat", "price": 300}, {"name": "Shoes", "price": 400}]}
        else:
            return {"error": "No query or description provided"}
        
def createTool(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper()

@createTool
def query_data():
    return AgentQLQueryDataTool()