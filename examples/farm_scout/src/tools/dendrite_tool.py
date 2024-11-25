from crewai_tools import tool
from dendrite import Dendrite


# This is a tool that allows the agent to ask a question to the browser.
def ask(url: str, question: str):
    """
    Ask a question to any page on the web. E.g "On this page, what is the current temperature?"
    """
    browser = Dendrite()
    browser.goto(url)
    return browser.ask(url, question)


# Obviously, this tool isn't useful for many people. (Unless you're a farmer.)
# It's just an example of how to use Dendrite to extract information from any website by using the SDK.
# Find a whole repo of examples here: https://github.com/dendrite-systems/dendrite-examples
@tool
def get_farm_land(min_price: int, max_price: int, min_acres: int, max_acres: int):
    """
    Example tool that uses Dendrite to extract farm land information from land.com to help the agent decide what land to buy.
    Args:
        min_price: The minimum price of the land to search for
        max_price: The maximum price of the land to search for
        min_acres: The minimum acres of the land to search for
        max_acres: The maximum acres of the land to search for
    Returns:
        an array of dicts like this [{'title': 'string', 'location': 'string', 'see_more_url': 'string', 'price': 'string', 'acres': 'string'}]
    """

    print(min_price, max_price, min_acres, max_acres)

    browser = Dendrite()
    browser.goto("https://www.land.com/United-States/all-land/")

    # Filter by price
    browser.click("price dropdown button")
    browser.fill_fields(
        {
            "min_price": min_price,
            "max_price": max_price,
        }
    )
    browser.press("Enter")

    # Filter by acres
    browser.click("acres dropdown button")
    browser.fill_fields(
        {
            "min_acres": min_acres,
            "max_acres": max_acres,
        }
    )
    browser.press("Enter")

    # Extract the results
    results = browser.extract(
        "Get all the results as an array of dicts like this [{'title': 'string', 'location': 'string', 'see_more_url': 'string', 'price': 'string', 'acres': 'string'}]"
    )
    return results


if __name__ == "__main__":
    print(get_farm_land(10000, 100000, 100, 1000))
