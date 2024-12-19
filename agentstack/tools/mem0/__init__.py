import os
import json
from mem0 import MemoryClient

# These functions can be extended by changing the user_id parameter
# Memories are sorted by user_id


MEM0_API_KEY = os.getenv('MEM0_API_KEY')
client = MemoryClient(api_key=MEM0_API_KEY)

# These tools will only save information about the user
# "Potato is a vegetable" is not a memory
# "My favorite food is potatoes" IS a memory


def write_to_memory(user_message: str) -> str:
    """
    Writes data to the memory store for a user. The tool will decide what
    specific information is important to store as memory.
    """
    messages = [
        {"role": "user", "content": user_message},
    ]
    result = client.add(messages, user_id='default')  # configure user
    return json.dumps(result)


def read_from_memory(query: str) -> str:
    """
    Reads memories related to user based on a query.
    """
    memories = client.search(query=query, user_id='default')
    if memories:
        return "\n".join([mem['memory'] for mem in memories])
    else:
        return "No relevant memories found."
