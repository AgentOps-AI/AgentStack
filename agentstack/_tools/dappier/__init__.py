import os
from typing import Optional, Literal
from dappier import Dappier

# Initialize the Dappier client
client = Dappier(api_key=os.getenv("DAPPIER_API_KEY"))

# --- Functions for AI Models ---


def real_time_web_search(query: str) -> str:
    """
    Perform a real-time web search. Access the latest news, stock market data, weather,
    travel information, deals, and more using this AI model. Use when no stock ticker symbol
    is provided.

    Args:
        query: The search query to retrieve real-time information.

    Returns:
        A formatted string containing real-time search results.
    """
    try:
        return client.search_real_time_data_string(query=query, ai_model_id="am_01j06ytn18ejftedz6dyhz2b15")
    except Exception as e:
        return f"Error: {str(e)}"


def stock_market_data_search(query: str) -> str:
    """
    Perform a real-time stock market data search. Retrieve real-time financial news,
    stock prices, and trade updates with AI-powered insights using this model. Use only when a
    stock ticker symbol is provided.

    Args:
        query: The search query to retrieve real-time stock market information.

    Returns:
        A formatted string containing real-time financial search results.
    """
    try:
        return client.search_real_time_data_string(query=query, ai_model_id="am_01j749h8pbf7ns8r1bq9s2evrh")
    except Exception as e:
        return f"Error: {str(e)}"


# --- Functions for Data Models ---


def get_sports_news(
    query: str,
    similarity_top_k: int = 9,
    ref: Optional[str] = None,
    num_articles_ref: int = 0,
    search_algorithm: Literal["most_recent", "semantic", "most_recent_semantic", "trending"] = "most_recent",
) -> str:
    """
    Fetch AI-powered Sports News recommendations. Get real-time news, updates, and personalized
    content from top sports sources like Sportsnaut, Forever Blueshirts, Minnesota Sports Fan,
    LAFB Network, Bounding Into Sports, and Ringside Intel.

    Args:
        query: The input string for sports-related content recommendations.
        similarity_top_k: Number of top similar articles to retrieve.
        ref: Optional site domain to prioritize recommendations.
        num_articles_ref: Minimum number of articles to return from the reference domain.
        search_algorithm: The search algorithm to use ('most_recent', 'semantic', 'most_recent_semantic', 'trending').

    Returns:
        A formatted string containing recommended sports articles.
    """
    try:
        return client.get_ai_recommendations_string(
            query=query,
            data_model_id="dm_01j0pb465keqmatq9k83dthx34",
            similarity_top_k=similarity_top_k,
            ref=ref or "",
            num_articles_ref=num_articles_ref,
            search_algorithm=search_algorithm,
        )
    except Exception as e:
        return f"Error: {str(e)}"


def get_lifestyle_news(
    query: str,
    similarity_top_k: int = 9,
    ref: Optional[str] = None,
    num_articles_ref: int = 0,
    search_algorithm: Literal["most_recent", "semantic", "most_recent_semantic", "trending"] = "most_recent",
) -> str:
    """
    Fetch AI-powered Lifestyle News recommendations. Access current lifestyle updates, analysis,
    and insights from leading lifestyle publications like The Mix, Snipdaily, Nerdable
    and Familyproof.

    Args:
        query: The input string for lifestyle-related content recommendations.
        similarity_top_k: Number of top similar articles to retrieve.
        ref: Optional site domain to prioritize recommendations.
        num_articles_ref: Minimum number of articles to return from the reference domain.
        search_algorithm: The search algorithm to use ('most_recent', 'semantic', 'most_recent_semantic', 'trending').

    Returns:
        A formatted string containing recommended lifestyle articles.
    """
    try:
        return client.get_ai_recommendations_string(
            query=query,
            data_model_id="dm_01j0q82s4bfjmsqkhs3ywm3x6y",
            similarity_top_k=similarity_top_k,
            ref=ref or "",
            num_articles_ref=num_articles_ref,
            search_algorithm=search_algorithm,
        )
    except Exception as e:
        return f"Error: {str(e)}"


def get_iheartdogs_content(
    query: str,
    similarity_top_k: int = 9,
    ref: Optional[str] = None,
    num_articles_ref: int = 0,
    search_algorithm: Literal["most_recent", "semantic", "most_recent_semantic", "trending"] = "most_recent",
) -> str:
    """
    Fetch AI-powered iHeartDogs content recommendations. Tap into a dog care expert with access
    to thousands of articles covering pet health, behavior, grooming, and ownership from
    iHeartDogs.com.

    Args:
        query: The input string for dog care-related content recommendations.
        similarity_top_k: Number of top similar articles to retrieve.
        ref: Optional site domain to prioritize recommendations.
        num_articles_ref: Minimum number of articles to return from the reference domain.
        search_algorithm: The search algorithm to use ('most_recent', 'semantic', 'most_recent_semantic', 'trending').

    Returns:
        A formatted string containing recommended dog-related articles.
    """
    try:
        return client.get_ai_recommendations_string(
            query=query,
            data_model_id="dm_01j1sz8t3qe6v9g8ad102kvmqn",
            similarity_top_k=similarity_top_k,
            ref=ref or "",
            num_articles_ref=num_articles_ref,
            search_algorithm=search_algorithm,
        )
    except Exception as e:
        return f"Error: {str(e)}"


def get_iheartcats_content(
    query: str,
    similarity_top_k: int = 9,
    ref: Optional[str] = None,
    num_articles_ref: int = 0,
    search_algorithm: Literal["most_recent", "semantic", "most_recent_semantic", "trending"] = "most_recent",
) -> str:
    """
    Fetch AI-powered iHeartCats content recommendations. Utilize a cat care specialist that
    provides comprehensive content on cat health, behavior, and lifestyle from iHeartCats.com.

    Args:
        query: The input string for cat care-related content recommendations.
        similarity_top_k: Number of top similar articles to retrieve.
        ref: Optional site domain to prioritize recommendations.
        num_articles_ref: Minimum number of articles to return from the reference domain.
        search_algorithm: The search algorithm to use ('most_recent', 'semantic', 'most_recent_semantic', 'trending').

    Returns:
        A formatted string containing recommended cat-related articles.
    """
    try:
        return client.get_ai_recommendations_string(
            query=query,
            data_model_id="dm_01j1sza0h7ekhaecys2p3y0vmj",
            similarity_top_k=similarity_top_k,
            ref=ref or "",
            num_articles_ref=num_articles_ref,
            search_algorithm=search_algorithm,
        )
    except Exception as e:
        return f"Error: {str(e)}"


def get_greenmonster_guides(
    query: str,
    similarity_top_k: int = 9,
    ref: Optional[str] = None,
    num_articles_ref: int = 0,
    search_algorithm: Literal["most_recent", "semantic", "most_recent_semantic", "trending"] = "most_recent",
) -> str:
    """
    Fetch AI-powered GreenMonster guides and articles. Receive guidance for making conscious
    and compassionate choices benefiting people, animals, and the planet.

    Args:
        query: The input string for eco-friendly and conscious lifestyle recommendations.
        similarity_top_k: Number of top similar articles to retrieve.
        ref: Optional site domain to prioritize recommendations.
        num_articles_ref: Minimum number of articles to return from the reference domain.
        search_algorithm: The search algorithm to use ('most_recent', 'semantic', 'most_recent_semantic', 'trending').

    Returns:
        A formatted string containing recommended eco-conscious articles.
    """
    try:
        return client.get_ai_recommendations_string(
            query=query,
            data_model_id="dm_01j5xy9w5sf49bm6b1prm80m27",
            similarity_top_k=similarity_top_k,
            ref=ref or "",
            num_articles_ref=num_articles_ref,
            search_algorithm=search_algorithm,
        )
    except Exception as e:
        return f"Error: {str(e)}"


def get_wishtv_news(
    query: str,
    similarity_top_k: int = 9,
    ref: Optional[str] = None,
    num_articles_ref: int = 0,
    search_algorithm: Literal["most_recent", "semantic", "most_recent_semantic", "trending"] = "most_recent",
) -> str:
    """
    Fetch AI-powered WISH-TV news recommendations. Get recommendations covering sports,
    breaking news, politics, multicultural updates, Hispanic language content, entertainment,
    health, and education.

    Args:
        query: The input string for general news recommendations.
        similarity_top_k: Number of top similar articles to retrieve.
        ref: Optional site domain to prioritize recommendations.
        num_articles_ref: Minimum number of articles to return from the reference domain.
        search_algorithm: The search algorithm to use ('most_recent', 'semantic', 'most_recent_semantic', 'trending').

    Returns:
        A formatted string containing recommended news articles.
    """
    try:
        return client.get_ai_recommendations_string(
            query=query,
            data_model_id="dm_01jagy9nqaeer9hxx8z1sk1jx6",
            similarity_top_k=similarity_top_k,
            ref=ref or "",
            num_articles_ref=num_articles_ref,
            search_algorithm=search_algorithm,
        )
    except Exception as e:
        return f"Error: {str(e)}"
