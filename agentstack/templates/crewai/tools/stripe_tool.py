import os
from stripe_agent_toolkit.crewai.toolkit import StripeAgentToolkit
from dotenv import load_dotenv
load_dotenv()

stripe_tools = StripeAgentToolkit(
    secret_key=os.getenv("STRIPE_SECRET_KEY"),
    configuration={
        "actions": {
            "payment_links": {
                "create": True,
                "read": True,
                "update": False
            },
            "products": {
                "create": True,
                "update": True
            },
            "prices": {
                "create": True,
                "update": True
            },
        }
    }).get_tools()
