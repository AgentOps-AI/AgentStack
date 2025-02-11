import os
from agentstack import tools
from exa_py import Exa

# Check out our docs for more info! https://docs.exa.ai/

API_KEY = os.getenv('EXA_API_KEY')


def search_and_contents(question: str) -> str:
    """
    Tool using Exa's Python SDK to run semantic search and return result highlights.
    Args:
        question: The search query or question to find information about
    Returns:
        Formatted string containing titles, URLs, and highlights from the search results
    """
    permissions = tools.get_permissions(search_and_contents)
    if not permissions.READ:
        return "User has not granted read permission."
    
    exa = Exa(api_key=API_KEY)
    response = exa.search_and_contents(
        question, type="neural", use_autoprompt=True, num_results=3, highlights=True
    )

    parsedResult = ''.join(
        [
            f'<Title id={idx}>{eachResult.title}</Title>'
            f'<URL id={idx}>{eachResult.url}</URL>'
            f'<Highlight id={idx}>{"".join(eachResult.highlights)}</Highlight>'
            for (idx, eachResult) in enumerate(response.results)
        ]
    )

    return parsedResult
