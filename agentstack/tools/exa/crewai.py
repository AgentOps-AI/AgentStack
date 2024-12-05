from crewai_tools import tool
from .common import search_and_contents as _search_and_contents


@tool("Exa search and get contents")
def search_and_contents(question: str) -> str:
    return _search_and_contents(question)

