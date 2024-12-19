"""Stripe tool for AgentStack.

This module provides framework-agnostic functions for interacting with the Stripe API,
supporting payment links, products, and prices operations.
"""

import json
import os
from typing import Dict, Optional

import stripe
from stripe_agent_toolkit.functions import (
    create_payment_link as toolkit_create_payment_link,
    create_product as toolkit_create_product,
    create_price as toolkit_create_price,
)
from stripe_agent_toolkit.configuration import Context
from stripe_agent_toolkit.schema import CreatePaymentLink, CreateProduct, CreatePrice


def setup_stripe(secret_key: str) -> None:
    """Initialize Stripe with the provided secret key."""
    stripe.api_key = secret_key
    stripe.set_app_info("agentstack-stripe", version="0.1.0", url="https://github.com/AgentOps-AI/AgentStack")


def create_payment_link(price: str, quantity: int) -> Dict:
    """Create a payment link for a specific price and quantity.

    Args:
        price: The ID of the price to create a payment link for
        quantity: The quantity of items to include in the payment link

    Returns:
        Dict containing the payment link ID and URL
    """
    # Validate input using toolkit's schema
    params = CreatePaymentLink(price=price, quantity=quantity)
    return toolkit_create_payment_link(Context(), params.price, params.quantity)


def get_payment_link(payment_link_id: str) -> Dict:
    """Retrieve a payment link by ID.

    Args:
        payment_link_id: The ID of the payment link to retrieve

    Returns:
        Dict containing the payment link ID and URL
    """
    payment_link = stripe.PaymentLink.retrieve(payment_link_id)
    return {"id": payment_link.id, "url": payment_link.url}


def create_product(name: str, description: Optional[str] = None) -> Dict:
    """Create a new product.

    Args:
        name: The name of the product
        description: Optional description of the product

    Returns:
        Dict containing the product details
    """
    # Validate input using toolkit's schema
    params = CreateProduct(name=name, description=description)
    return toolkit_create_product(Context(), params.name, params.description)


def update_product(product_id: str, **kwargs) -> Dict:
    """Update an existing product.

    Args:
        product_id: The ID of the product to update
        **kwargs: Additional fields to update (e.g., name, description)

    Returns:
        Dict containing the updated product details
    """
    product = stripe.Product.modify(product_id, **kwargs)
    return json.loads(str(product))


def create_price(product: str, currency: str, unit_amount: int) -> Dict:
    """Create a new price for a product.

    Args:
        product: The ID of the product to create a price for
        currency: Three-letter ISO currency code
        unit_amount: The amount in cents to charge

    Returns:
        Dict containing the price details
    """
    # Validate input using toolkit's schema
    params = CreatePrice(product=product, currency=currency, unit_amount=unit_amount)
    return toolkit_create_price(Context(), params.product, params.currency, params.unit_amount)


def update_price(price_id: str, **kwargs) -> Dict:
    """Update an existing price.

    Args:
        price_id: The ID of the price to update
        **kwargs: Additional fields to update (e.g., nickname, active)

    Returns:
        Dict containing the updated price details
    """
    price = stripe.Price.modify(price_id, **kwargs)
    return json.loads(str(price))


# Initialize Stripe when the module is imported if the environment variable is set
if "STRIPE_SECRET_KEY" in os.environ:
    setup_stripe(os.environ["STRIPE_SECRET_KEY"])
