"""
Implementation of the cognee for AgentStack.
These functions wrap cognee's asynchronous methods and expose them
as synchronous functions with typed parameters & docstrings for use by AI agents.
"""

import cognee
import asyncio
from typing import List
from cognee.api.v1.search import SearchType


def prune_data(metadata: bool = False) -> str:
    """
    Prune the cognee data. If metadata is True, also prune system metadata.

    :param metadata: Whether to prune system metadata as well.
    :return: A confirmation message.
    """

    async def _prune():
        await cognee.prune.prune_data()
        if metadata:
            await cognee.prune.prune_system(metadata=True)
        return "Data pruned successfully."

    return asyncio.run(_prune())


def add_text(text: str) -> str:
    """
    Add text to cognee's knowledge system for future 'cognify' operations.

    :param text: The text to add.
    :return: A confirmation message.
    """

    async def _add():
        await cognee.add(text)
        return "Text added successfully."

    return asyncio.run(_add())


def cognify() -> str:
    """
    Run cognee's 'cognify' pipeline to build the knowledge graph,
    summaries, and other metadata from previously added text.

    :return: A confirmation message.
    """

    async def _cognify():
        await cognee.cognify()
        return "Cognify process complete."

    return asyncio.run(_cognify())


def search_insights(query_text: str) -> str:
    """
    Perform an INSIGHTS search on the knowledge graph for the given query text.

    :param query_text: The query to search for.
    :return: The search results as a (stringified) list of matches.
    """

    async def _search():
        results = await cognee.search(SearchType.INSIGHTS, query_text=query_text)
        return str(results)

    return asyncio.run(_search())

def search_summaries(query_text: str) -> str:
    """
    Perform a SUMMARIES search on the knowledge graph for the given query text.

    :param query_text: The query to search for.
    :return: The search results as a (stringified) list of matches.
    """

    async def _search():
        results = await cognee.search(SearchType.SUMMARIES, query_text=query_text)
        return str(results)

    return asyncio.run(_search())

def search_chunks(query_text: str) -> str:
    """
    Perform a CHUNKS search on the knowledge graph for the given query text.

    :param query_text: The query to search for.
    :return: The search results as a (stringified) list of matches.
    """

    async def _search():
        results = await cognee.search(SearchType.CHUNKS, query_text=query_text)
        return str(results)

    return asyncio.run(_search())

def search_completion(query_text: str) -> str:
    """
    Perform a COMPLETION search on the knowledge graph for the given query text.

    :param query_text: The query to search for.
    :return: The search results as a (stringified) list of matches.
    """

    async def _search():
        results = await cognee.search(SearchType.COMPLETION, query_text=query_text)
        return str(results)

    return asyncio.run(_search())

def search_graph_completion(query_text: str) -> str:
    """
    Perform a GRAPH_COMPLETION search on the knowledge graph for the given query text.

    :param query_text: The query to search for.
    :return: The search results as a (stringified) list of matches.
    """

    async def _search():
        results = await cognee.search(SearchType.GRAPH_COMPLETION, query_text=query_text)
        return str(results)

    return asyncio.run(_search())