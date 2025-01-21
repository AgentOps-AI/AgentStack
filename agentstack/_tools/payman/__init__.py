import os
from typing import Dict, List, Optional, Union, Literal
from paymanai import Paymanai

# Initialize Payman client
PAYMAN_API_SECRET = os.getenv("PAYMAN_API_SECRET")
PAYMAN_ENVIRONMENT = os.getenv("PAYMAN_ENVIRONMENT")

client = Paymanai(
    x_payman_api_secret=PAYMAN_API_SECRET,
    environment=PAYMAN_ENVIRONMENT
)

def send_payment(
    amount_decimal: float,
    payment_destination_id: Optional[str] = None,
    payment_destination: Optional[Dict] = None,
    customer_id: Optional[str] = None,
    customer_email: Optional[str] = None,
    customer_name: Optional[str] = None,
    memo: Optional[str] = None
) -> Dict:
    """
    Send a payment using Payman.
    
    Args:
        amount_decimal: Amount to send in decimal format
        payment_destination_id: ID of existing payment destination
        payment_destination: Dictionary containing payment destination details
        customer_id: Optional customer ID
        customer_email: Optional customer email
        customer_name: Optional customer name
        memo: Optional payment memo
    
    Returns:
        Dictionary containing payment details
    """
    try:
        return client.payments.send_payment(
            amount_decimal=amount_decimal,
            payment_destination_id=payment_destination_id,
            payment_destination=payment_destination,
            customer_id=customer_id,
            customer_email=customer_email,
            customer_name=customer_name,
            memo=memo
        )
    except Exception as e:
        return {"error": f"Failed to send payment: {str(e)}"}

def search_available_payees(
    name: Optional[str] = None,
    contact_email: Optional[str] = None,
    type: Optional[str] = None
) -> List[Dict]:
    """
    Search for available payment destinations/payees.
    
    Args:
        name: Optional name filter
        contact_email: Optional email filter
        type: Optional payment type filter
    
    Returns:
        List of matching payment destinations
    """
    try:
        return client.payments.search_payees(
            name=name,
            contact_email=contact_email,
            type=type
        )
    except Exception as e:
        return [{"error": f"Failed to search payees: {str(e)}"}]

def add_payee(
    type: Literal["CRYPTO_ADDRESS"] | Literal["US_ACH"],
    name: Optional[str] = None,
    contact_details: Optional[Dict] = None,
    account_holder_name: Optional[str] = None,
    account_number: Optional[str] = None,
    account_type: Optional[str] = None,
    routing_number: Optional[str] = None,
    address: Optional[str] = None,
    currency: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict:
    """
    Add a new payee/payment destination.
    
    Args:
        type: Type of payment destination ("CRYPTO_ADDRESS" or "US_ACH")
        name: Optional name for the payment destination
        contact_details: Optional dictionary containing contact information
        account_holder_name: Required for US_ACH
        account_number: Required for US_ACH
        account_type: Required for US_ACH
        routing_number: Required for US_ACH
        address: Required for CRYPTO_ADDRESS
        currency: Optional currency specification
        tags: Optional list of tags
    
    Returns:
        Dictionary containing the created payee details
    """
    try:
        return client.payments.create_payee(
            type=type,
            name=name,
            contact_details=contact_details,
            account_holder_name=account_holder_name,
            account_number=account_number,
            account_type=account_type,
            routing_number=routing_number,
            address=address,
            currency=currency,
            tags=tags
        )
    except Exception as e:
        return {"error": f"Failed to add payee: {str(e)}"}

def ask_for_money(
    amount_decimal: float,
    customer_id: str,
    customer_email: Optional[str] = None,
    customer_name: Optional[str] = None,
    memo: Optional[str] = None
) -> Dict:
    """
    Generate a checkout link to request money from a customer.
    
    Args:
        amount_decimal: Amount to request in decimal format
        customer_id: Customer's ID
        customer_email: Optional customer email
        customer_name: Optional customer name
        memo: Optional memo for the request
    
    Returns:
        Dictionary containing the checkout URL
    """
    try:
        response = client.payments.initiate_customer_deposit(
            amount_decimal=amount_decimal,
            customer_id=customer_id,
            customer_email=customer_email,
            customer_name=customer_name,
            memo=memo
        )
        return {"checkout_url": response.checkout_url}
    except Exception as e:
        return {"error": f"Failed to generate payment request: {str(e)}"}

def get_balance(
    customer_id: Optional[str] = None,
    currency: str = "USD"
) -> Dict:
    """
    Get balance information.
    
    Args:
        customer_id: Optional customer ID (if None, returns agent balance)
        currency: Currency to check balance for
    
    Returns:
        Dictionary containing balance information
    """
    try:
        if customer_id and customer_id.lower() != "none":
            return client.balances.get_customer_balance(
                customer_id=customer_id,  # Use keyword arguments
                currency=currency
            )
        return client.balances.get_spendable_balance(
            currency=currency
        )
    except Exception as e:
        return {"error": f"Failed to get balance: {str(e)}"}