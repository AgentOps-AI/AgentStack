from typing import Callable, Optional
import os, sys
from stripe_agent_toolkit.configuration import Configuration, is_tool_allowed
from stripe_agent_toolkit.api import StripeAPI
from stripe_agent_toolkit.tools import tools

__all__ = [
    "create_payment_link",
    "create_product",
    "list_products",
    "create_price",
    "list_prices",
]

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

if not STRIPE_SECRET_KEY:
    raise Exception(
        "Stripe Secret Key not found. Did you set the STRIPE_SECRET_KEY in you project's .env file?"
    )

_configuration = Configuration(
    {
        "actions": {
            "payment_links": {
                "create": True,
            },
            "products": {
                "create": True,
                "read": True,
            },
            "prices": {
                "create": True,
                "read": True,
            },
        }
    }
)
client = StripeAPI(
    secret_key=STRIPE_SECRET_KEY,
    context=_configuration.get('context') or None,
)


def _create_tool_function(tool: dict) -> Callable:
    """Dynamically create a tool function based on the tool schema."""
    # `tool` is not typed, but follows this schema:
    # {
    #     "method": "create_customer",
    #     "name": "Create Customer",
    #     "description": CREATE_CUSTOMER_PROMPT,
    #     "args_schema": CreateCustomer,
    #     "actions": {
    #         "customers": {
    #             "create": True,
    #         }
    #     },
    # }
    schema = tool['args_schema']

    def func(**kwargs) -> str:
        validated_data = schema(**kwargs)
        return client.run(tool['method'], **validated_data.dict(exclude_unset=True))

    func.__name__ = tool['method']
    func.__doc__ = f"{tool['name']}: \n{tool['description']}"
    func.__annotations__ = {
        'return': str,
        **{name: field.annotation for name, field in schema.model_fields.items()},
    }
    return func


# Dynamically create tool functions based on the configuration and add them to the module.
for tool in tools:
    if not is_tool_allowed(tool, _configuration):
        continue

    setattr(sys.modules[__name__], tool['method'], _create_tool_function(tool))
