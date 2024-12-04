from crewai_tools import tool
from .common import execute_code

execute_code = tool("Execute Code")(execute_code)
