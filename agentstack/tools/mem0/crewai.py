from crewai_tools import tool
from .common import write_to_memory, read_from_memory

write_to_memory = tool("Write to Memory")(write_to_memory)
read_from_memory = tool("Read from Memory")(read_from_memory)
