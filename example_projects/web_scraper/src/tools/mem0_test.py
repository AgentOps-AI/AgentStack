from crewai_tools import tool
from mem0 import Memory
from dotenv import load_dotenv
import os
from mem0 import MemoryClient
import chromadb
chroma_client = chromadb.Client()

load_dotenv()

MEM0_API_KEY = os.getenv('MEM0_API_KEY', 'm0-bQFbUJO49Ydz3LAKhEyjOx6SomgCANmvauk4vaXu')
client = MemoryClient(api_key=MEM0_API_KEY)

# config = {
#     "vector_store": {
#         "provider": "chroma",
#         "config": {
#             "collection_name": "test",
#             "path": "db",
#         }
#     },
#     "version": "v1.1"
# }

m = Memory()

config = {
    # "graph_store": {
    #     "provider": "neo4j",
    #     "config": {
    #         "url": 'neo4j+s://a67f9a12.databases.neo4j.io',
    #         "username": 'neo4j',
    #         "password": 'ndGFALFrHSpb_KxwOcHTOMw1gILuJHSmczlrmFx6tc8',
    #     }
    # },
    "version": "v1.1"
}

# memory = Memory.from_config(config)

messages = [
    {"role": "user", "content": "Hi, I'm Alex. I'm a vegetarian and I'm allergic to nuts."},
    {"role": "assistant", "content": "Hello Alex! I've noted that you're a vegetarian and have a nut allergy. I'll keep this in mind for any food-related recommendations or discussions."}
]
result = client.add(messages, user_id="default")
# result = m.add("do you believe in life after love?", user_id="default")
print('result')
print(result)

# memories = memory.search(query="love", user_id="default")
# memories = m.search(query="love", user_id="default")
memories = client.get_all(user_id="default")
print('memories')
print(memories)