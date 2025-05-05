import os
from typing import List

from hyperbrowser import Hyperbrowser
from hyperbrowser.models import (
    BrowserUseTaskResponse,
    ClaudeComputerUseTaskResponse,
    CrawlJobResponse,
    CreateSessionParams,
    CuaTaskResponse,
    ExtractJobResponse,
    ScrapeFormat,
    ScrapeJobResponse,
    ScrapeOptions,
    StartBrowserUseTaskParams,
    StartClaudeComputerUseTaskParams,
    StartCrawlJobParams,
    StartCuaTaskParams,
    StartExtractJobParams,
    StartScrapeJobParams,
)

hb = Hyperbrowser(api_key=os.getenv('HYPERBROWSER_API_KEY'))


def scrape_webpage(
    url: str, use_proxy: bool = True, formats: list[ScrapeFormat] = ["markdown"]
) -> ScrapeJobResponse:
    """
    Scrapes content from a single webpage in specified formats.

    This function initiates a scraping job for a given URL and waits for completion.
    It configures a browser session with proxy and stealth options for optimal scraping.

    Args:
        url: The URL of the webpage to scrape
        use_proxy: Whether to use a proxy for the request (default: True)
        formats: List of formats to return the scraped content in (default: ["markdown"])
                 Options include "markdown", "html", "links", "screenshot"

    Returns:
        ScrapeJobResponse: The response containing the scraped content in requested formats
    """
    return hb.scrape.start_and_wait(
        StartScrapeJobParams(
            url=url,
            session_options=CreateSessionParams(
                use_proxy=use_proxy,
                use_stealth=True,
                adblock=True,
                trackers=True,
                annoyances=True,
            ),
            scrape_options=ScrapeOptions(
                formats=formats,
            ),
        )
    )


def crawl_website(
    starting_url: str,
    max_pages: int = 10,
    include_pattern: List[str] = [],
    exclude_pattern: List[str] = [],
    use_proxy: bool = True,
) -> CrawlJobResponse:
    """
    Crawls a website starting from a specific URL and collects content from multiple pages.

    This function navigates through a website by following links from the starting URL,
    up to the specified maximum number of pages. It can filter pages to crawl based on
    include and exclude patterns.

    Args:
        starting_url: The initial URL to start crawling from
        max_pages: Maximum number of pages to crawl (default: 10)
        include_pattern: List of patterns for URLs to include in the crawl (default: [])
        exclude_pattern: List of patterns for URLs to exclude from the crawl (default: [])
        use_proxy: Whether to use a proxy for the requests (default: True)

    Returns:
        CrawlJobResponse: The response containing the crawled content from all visited pages
    """
    return hb.crawl.start_and_wait(
        StartCrawlJobParams(
            url=starting_url,
            max_pages=max_pages,
            include_pattern=include_pattern,
            exclude_pattern=exclude_pattern,
            session_options=CreateSessionParams(
                use_proxy=use_proxy,
                use_stealth=True,
                adblock=True,
                trackers=True,
                annoyances=True,
            ),
        )
    )


def extract_data_from_webpages(
    urls: List[str],
    schema: str,
    prompt: str,
    system_prompt: str | None = None,
    use_proxy: bool = True,
) -> ExtractJobResponse:
    """
    Extracts structured data from multiple webpages based on a provided schema and prompt.

    This function visits each URL in the list and extracts structured data according to the
    specified schema and guided by the provided prompt. It uses AI-powered extraction to
    transform unstructured web content into structured data.

    Args:
        urls: List of URLs to extract data from
        schema: JSON schema that defines the structure of the data to extract
        prompt: Instructions for the extraction model on what data to extract
        system_prompt: Optional system prompt to further guide the extraction (default: None)
        use_proxy: Whether to use a proxy for the requests (default: True)

    Returns:
        ExtractJobResponse: The response containing the extracted structured data from all URLs
    """
    return hb.extract.start_and_wait(
        StartExtractJobParams(
            urls=urls,
            prompt=prompt,
            system_prompt=system_prompt,
            schema=schema,
            session_options=CreateSessionParams(
                use_proxy=use_proxy,
                use_stealth=True,
                adblock=True,
            ),
        )
    )


def run_browser_use_agent(
    task: str,
    max_steps: int = 10,
    use_vision: bool = False,
    use_vision_for_planner: bool = False,
    use_proxy: bool = True,
) -> BrowserUseTaskResponse:
    """
    Runs a lightweight browser automation agent to perform a specific task.

    This function initiates a browser session and runs a specialized agent that
    performs the specified task with minimal overhead. This agent is optimized for
    speed and efficiency but requires explicit, detailed instructions.

    Args:
        task: Detailed description of the task to perform
        max_steps: Maximum number of steps the agent can take (default: 10)
        use_vision: Whether to enable vision capabilities for the agent (default: False)
        use_vision_for_planner: Whether to use vision for planning steps (default: False)
        use_proxy: Whether to use a proxy for the browser session (default: True)

    Returns:
        BrowserUseTaskResponse: The response containing the results of the task execution
    """
    return hb.agents.browser_use.start_and_wait(
        StartBrowserUseTaskParams(
            task=task,
            max_steps=max_steps,
            use_vision=use_vision,
            use_vision_for_planner=use_vision_for_planner,
            session_options=CreateSessionParams(
                use_proxy=use_proxy,
                use_stealth=True,
                adblock=True,
                trackers=True,
                annoyances=True,
            ),
        )
    )


def run_claude_computer_use_agent(
    task: str,
    max_steps: int = 10,
    use_vision: bool = False,
    use_vision_for_planner: bool = False,
    use_proxy: bool = True,
) -> ClaudeComputerUseTaskResponse:
    """
    Runs a Claude-powered browser automation agent to perform complex tasks.

    This function initiates a browser session with Anthropic's Claude model as the
    driving intelligence. The agent is capable of sophisticated reasoning and handling
    complex, nuanced tasks that require understanding context and making decisions.

    Args:
        task: Description of the task to perform
        max_steps: Maximum number of steps the agent can take (default: 10)
        use_vision: Whether to enable vision capabilities for the agent (default: False)
        use_vision_for_planner: Whether to use vision for planning steps (default: False)
        use_proxy: Whether to use a proxy for the browser session (default: True)

    Returns:
        ClaudeComputerUseTaskResponse: The response containing the results of the task execution
    """
    return hb.agents.claude_computer_use.start_and_wait(
        StartClaudeComputerUseTaskParams(
            task=task,
            max_steps=max_steps,
            use_vision=use_vision,
            use_vision_for_planner=use_vision_for_planner,
            session_options=CreateSessionParams(
                use_proxy=use_proxy,
                use_stealth=True,
                adblock=True,
                trackers=True,
                annoyances=True,
            ),
        )
    )


def run_openai_cua_agent(
    task: str,
    max_steps: int = 10,
    use_vision: bool = False,
    use_vision_for_planner: bool = False,
    use_proxy: bool = True,
) -> CuaTaskResponse:
    """
    Runs an OpenAI-powered browser automation agent to perform general-purpose tasks.

    This function initiates a browser session with OpenAI's model as the driving
    intelligence. The agent provides balanced performance and reliability for a wide range
    of browser automation tasks with moderate complexity.

    Args:
        task: Description of the task to perform
        max_steps: Maximum number of steps the agent can take (default: 10)
        use_vision: Whether to enable vision capabilities for the agent (default: False)
        use_vision_for_planner: Whether to use vision for planning steps (default: False)
        use_proxy: Whether to use a proxy for the browser session (default: True)

    Returns:
        CuaTaskResponse: The response containing the results of the task execution
    """
    return hb.agents.cua.start_and_wait(
        StartCuaTaskParams(
            task=task,
            max_steps=max_steps,
            use_vision=use_vision,
            use_vision_for_planner=use_vision_for_planner,
            session_options=CreateSessionParams(
                use_proxy=use_proxy,
                use_stealth=True,
                adblock=True,
                trackers=True,
                annoyances=True,
            ),
        )
    )
