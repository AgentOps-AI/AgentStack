from crewai_tools import tool
from .common import (
    web_scrape as _web_scrape, 
    web_crawl as _web_crawl, 
    retrieve_web_crawl as _retrieve_web_crawl, 
)


@tool("Web Scrape")
def web_scrape(url: str):
    return _web_scrape(url)


@tool("Web Crawl")
def web_crawl(url: str):
    return _web_crawl(url)


@tool("Retrieve Web Crawl")
def retrieve_web_crawl(crawl_id: str):
    return _retrieve_web_crawl(crawl_id)

