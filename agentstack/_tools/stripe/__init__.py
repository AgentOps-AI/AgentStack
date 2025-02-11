from typing import Callable, Optional
import os, sys
from stripe_agent_toolkit.configuration import Configuration, is_tool_allowed
from stripe_agent_toolkit.api import StripeAPI
from stripe_agent_toolkit.tools import tools
import agentstack


STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

if not STRIPE_SECRET_KEY:
    raise Exception(
        "Stripe Secret Key not found. Did you set the STRIPE_SECRET_KEY in you project's .env file?"
    )

tool_config = agentstack.get_tool('stripe')


def tool_can_read(tool_name: str) -> bool:
    """Check if the tool can read a specific resource."""
    try:
        return tool_config.tools[tool_name].READ
    except KeyError:
        return False


def tool_can_write(tool_name: str) -> bool:
    """Check if the tool can write to a specific resource."""
    try:
        return tool_config.tools[tool_name].WRITE
    except KeyError:
        return False

# in order to leverage as much of the offerings of stripe-agent-toolkit as 
# possible, we merge our configuration patterns with theirs
_configuration = Configuration(
    {
        "actions": {
            "balance": {
                "read": tool_can_read('retrieve_balance'),
            },
            "customers": {
                "create": tool_can_write('create_customer'),
                "read": tool_can_read('list_customers'),
            },
            "invoices": {
                "create": tool_can_write('create_invoice'),
                "update": tool_can_write('finalize_invoice'),
            },
            "invoice_items": {
                "create": tool_can_write('create_invoice_item'),
            },
            "payment_links": {
                "create": tool_can_write('create_payment_link'),
            },
            "products": {
                "create": tool_can_write('create_product'),
                "read": tool_can_read('list_products'),
            },
            "prices": {
                "create": tool_can_write('create_price'),
                "read": tool_can_read('list_prices'),
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
    # stripe-agent-toolkit exposes tools as classes by default, this utilizes
    # the typing and tooling in a functional way.
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
