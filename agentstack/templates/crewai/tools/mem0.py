from crewai_tools import tool
from mem0 import Memory
from dotenv import load_dotenv
import os

load_dotenv()

# Optionally configure mem0 to use any other store
# https://docs.mem0.ai/components/vectordbs/config#config
config = {
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": os.getenv("NEO4J_URL"),
            "username": os.getenv("NEO4J_USERNAME", 'neo4j'),
            "password": os.getenv("NEO4J_PASSWORD"),
        }
    },
    "version": "v1.1"
}

memory = Memory.from_config(config)

# These functions can be extended by taking an optional user_id parameter
# https://docs.mem0.ai/integrations/multion#add-memories-to-mem0


@tool("Write to Memory")
def write_to_memory(data: str) -> str:
    """Writes data to the memory store"""
    result = memory.add(data)
    return f"Memory added with ID: {result['id']}"


@tool("Read from Memory")
def read_from_memory(query: str) -> str:
    """Reads memories based on a query."""
    memories = memory.search(query=query)
    if memories["memories"]:
        return "\n".join([mem["data"] for mem in memories["memories"]])
    else:
        return "No relevant memories found."
