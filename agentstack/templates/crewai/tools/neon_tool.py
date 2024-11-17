import os
from crewai_tools import tool
from dotenv import load_dotenv
from neon import Neon

load_dotenv()

NEON_API_KEY = os.getenv('NEON_API_KEY')
neon_client = Neon(api_key=NEON_API_KEY)

# TODO: Should I duplicate this from the web_researcher example? Or is it
# possible to somehow have the web_researcher example import this?