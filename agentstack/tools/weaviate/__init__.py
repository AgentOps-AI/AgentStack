import os
import json
import weaviate
from typing import Optional
from weaviate.classes.config import Configure
from weaviate.classes.init import Auth

# Required environment variables
url = os.getenv("WEAVIATE_URL")
api_key = os.getenv("WEAVIATE_API_KEY")
openai_key = os.getenv("WEAVIATE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

if not url:
    raise Exception((
        "Weaviate URL has not been provided.\n"
        "Did you set the WEAVIATE_URL in your project's .env file?"
    ))

if not api_key:
    raise Exception((
        "Weaviate API key has not been provided.\n"
        "Did you set the WEAVIATE_API_KEY in your project's .env file?"
    ))

if not openai_key:
    raise Exception((
        "OpenAI API key has not been provided.\n"
        "Did you set either WEAVIATE_OPENAI_API_KEY or OPENAI_API_KEY in your project's .env file?"
    ))

def search_collection(
    collection_name: str,
    query: str,
    limit: int = 3,
    model: str = "nomic-embed-text"
) -> str:
    """Search a Weaviate collection using near-text queries.

    Args:
        collection_name: Name of the collection to search
        query: The search query
        limit: Maximum number of results (default: 3)
        model: Text embedding model to use (default: nomic-embed-text)

    Returns:
        str: JSON string containing search results
    """
    headers = {"X-OpenAI-Api-Key": openai_key}
    vectorizer = Configure.Vectorizer.text2vec_openai(model=model)

    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=url,
        auth_credentials=Auth.api_key(api_key),
        headers=headers
    )

    try:
        collection = client.collections.get(collection_name)
        if not collection:
            raise ValueError(f"Collection {collection_name} not found")

        response = collection.query.near_text(
            query=query,
            limit=limit
        )

        results = []
        for obj in response.objects:
            results.append(obj.properties)

        return json.dumps(results, indent=2)
    finally:
        client.close()

def create_collection(
    collection_name: str,
    model: str = "nomic-embed-text"
) -> str:
    """Create a new Weaviate collection.

    Args:
        collection_name: Name of the collection to create
        model: Text embedding model to use (default: nomic-embed-text)

    Returns:
        str: Success message
    """
    headers = {"X-OpenAI-Api-Key": openai_key}
    vectorizer = Configure.Vectorizer.text2vec_openai(model=model)

    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=url,
        auth_credentials=Auth.api_key(api_key),
        headers=headers
    )

    try:
        collection = client.collections.get(collection_name)
        if collection:
            return f"Collection {collection_name} already exists"

        client.collections.create(
            name=collection_name,
            vectorizer_config=vectorizer
        )
        return f"Created collection {collection_name}"
    finally:
        client.close()
