import os
from typing import Optional, Any
from browserbase import Browserbase


BROWSERBASE_API_KEY = os.getenv("BROWSERBASE_API_KEY")
BROWSERBASE_PROJECT_ID = os.getenv("BROWSERBASE_PROJECT_ID")

client = Browserbase(BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID)


# TODO can we define a type for the return value?
def load_url(
    url: str,
    text_content: Optional[bool] = True,
    session_id: Optional[str] = None,
    proxy: Optional[bool] = None,
) -> Any:
    """
    Load a URL in a headless browser and return the page content.

    Args:
        url: URL to load
        text_content: Return text content if True, otherwise return raw content
        session_id: Session ID to use for the browser
        proxy: Use a proxy for the browser
    Returns:
        Any: Page content
    """
    return client.load_url(url)
