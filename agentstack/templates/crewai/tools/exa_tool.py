from crewai_tools import tool
from exa_py import Exa
from dotenv import load_dotenv
import os

load_dotenv()

# Check out our docs for more info! https://docs.exa.ai/
@tool("Exa search and get contents")
def search_and_contents(question: str) -> str:
    """
    Tool using Exa's Python SDK to run semantic search and return result highlights.
    Args:
        question: The search query or question to find information about
    Returns:
        Formatted string containing titles, URLs, and highlights from the search results
    """
    exa = Exa(api_key=os.getenv('EXA_API_KEY'))

    response = exa.search_and_contents(
        question,
        type="neural",
        use_autoprompt=True,
        num_results=3,
        highlights=True
    )

    parsedResult = ''.join([
        f'<Title id={idx}>{eachResult.title}</Title>'
        f'<URL id={idx}>{eachResult.url}</URL>'
        f'<Highlight id={idx}>{"".join(eachResult.highlights)}</Highlight>' 
        for (idx, eachResult) in enumerate(response.results)
    ])

    return parsedResult
