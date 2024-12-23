import os
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key=os.getenv('FIRECRAWL_API_KEY'))


def web_scrape(url: str):
    """
    Scrape a url and return markdown. Use this to read a singular page and web_crawl only if you
    need to read all other links as well.
    """
    scrape_result = app.scrape_url(url, params={'formats': ['markdown']})
    return scrape_result


def web_crawl(url: str):
    """
    Scrape a url and crawl through other links from that page, scraping their contents.
    This tool returns a crawl_id that you will need to use after waiting for a period of time
    to retrieve the final contents. You should attempt to accomplish another task while waiting
    for the crawl to complete.

    Crawl will ignore sublinks of a page if they aren’t children of the url you provide.
    So, the website.com/other-parent/blog-1 wouldn’t be returned if you crawled website.com/blogs/.
    """

    crawl_status = app.crawl_url(
        url, params={'limit': 100, 'scrapeOptions': {'formats': ['markdown']}}, poll_interval=30
    )

    return crawl_status


def retrieve_web_crawl(crawl_id: str):
    """
    Retrieve the results of a previously started web crawl. Crawls take time to process
    so be sure to only use this tool some time after initiating a crawl. The result
    will tell you if the crawl is finished. If it is not, wait some more time then try again.
    """
    return app.check_crawl_status(crawl_id)
