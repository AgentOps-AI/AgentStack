from crewai_tools import tool
from .common import query_perplexity

query_perplexity = tool("Query Perplexity")(query_perplexity)
