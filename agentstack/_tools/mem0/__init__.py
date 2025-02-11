import os
import json
from agentstack import tools
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
    permissions = tools.get_permissions(write_to_memory)
    if not permissions.WRITE:
        return "User has not granted write permission."
    
    messages = [
        {"role": "user", "content": user_message},
    ]
    result = client.add(messages, user_id='default')  # configure user
    return json.dumps(result)


def read_from_memory(query: str) -> str:
    """
    Reads memories related to user based on a query.
    """
    permission = tools.get_permissions(read_from_memory)
    if not permission.READ:
        return "User has not granted read permission."
    
    memories = client.search(query=query, user_id='default')
    if memories:
        return "\n".join([mem['memory'] for mem in memories])
    else:
        return "No relevant memories found."
