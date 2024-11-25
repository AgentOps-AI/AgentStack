from crewai_tools import tool
from dendrite import Dendrite


# This is a tool that allows the agent to ask a question to the browser.
@tool
def ask(url: str, question: str):
    """
    Ask a question to any page on the web. E.g "On this page, what is the current temperature?"
    """
    browser = Dendrite()
    browser.goto(url)
    return browser.ask(url, question)
