import json

from crewai_tools import tool
from mem0 import MemoryClient
from dotenv import load_dotenv
import os

load_dotenv()

# Optionally configure mem0 to use any other store
# https://docs.mem0.ai/components/vectordbs/config#config
# config = {
#     "graph_store": {
#         "provider": "neo4j",
#         "config": {
#             "url": os.getenv("NEO4J_URL"),
#             "username": os.getenv("NEO4J_USERNAME", 'neo4j'),
#             "password": os.getenv("NEO4J_PASSWORD"),
#         }
#     },
#     "version": "v1.1"
# }

# memory = Memory.from_config(config)

# These functions can be extended by taking a user_id parameter
# https://docs.mem0.ai/integrations/multion#add-memories-to-mem0

MEM0_API_KEY = os.getenv('MEM0_API_KEY')
client = MemoryClient(api_key=MEM0_API_KEY)


# These tools will only save information about the user
# "Potato is a vegetable" is not a memory
# "My favorite food is potatoes" IS a memory

@tool("Write to Memory")
def write_to_memory(data: str) -> str:
    """
    Writes data to the memory store for a user
    """
    messages = [
        {"role": "user", "content": data},
    ]
    result = client.add(messages, user_id='default')  # configure user
    return json.dumps(result)


@tool("Read from Memory")
def read_from_memory(query: str) -> str:
    """
    Reads memories related to user based on a query.
    """
    memories = client.search(query=query, user_id='default')
    if memories:
        return "\n".join([mem['memory'] for mem in memories])
    else:
        return "No relevant memories found."
