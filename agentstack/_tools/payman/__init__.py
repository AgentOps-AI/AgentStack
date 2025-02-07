import os
from typing import Dict, List, Optional, Union, Literal
from paymanai import Paymanai

# Initialize Payman client
PAYMAN_API_SECRET = os.getenv("PAYMAN_API_SECRET")
PAYMAN_ENVIRONMENT = os.getenv("PAYMAN_ENVIRONMENT", "sandbox")

client = Paymanai(
    x_payman_api_secret=PAYMAN_API_SECRET,
    environment=PAYMAN_ENVIRONMENT
)

def send_payment(
    amount_decimal: float,
    payment_destination_id: str,
    customer_email: Optional[str] = None,
    customer_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    memo: Optional[str] = None
) -> Dict:
    """
    Send USD from the agent's wallet to a pre-created payment destination.
    
    Args:
        amount_decimal: Amount to send in USD (e.g. 10.00 for $10.00)
        payment_destination_id: ID of the pre-created payment destination
        customer_email: Optional email address of the customer
        customer_id: Optional ID of the customer
        customer_name: Optional name of the customer
        memo: Optional note or memo for the payment
    
    Returns:
        Dictionary containing payment details
    """
    try:
        return client.payments.send_payment(
            amount_decimal=amount_decimal,
            payment_destination_id=payment_destination_id,
            customer_email=customer_email,
            customer_id=customer_id,
            customer_name=customer_name,
            memo=memo
        )
    except Exception as e:
        return {"error": f"Failed to send payment: {str(e)}"}

def search_destinations(
    name: Optional[str] = None,
    customer_id: Optional[str] = None,
    contact_email: Optional[str] = None,
) -> List[Dict]:
    """
    Search for existing payment destinations by name, customer, or email.
    
    Args:
        name: Optional name of the payment destination
        customer_id: Optional customer ID who owns the destination
        contact_email: Optional contact email to search for
    
    Returns:
        List of matching payment destinations with their IDs
    """
    try:
        return client.payments.search_destinations(
            name=name,
            customer_id=customer_id,
            contact_email=contact_email
        )
    except Exception as e:
        return [{"error": f"Failed to search destinations: {str(e)}"}]

def create_payee(
    type: Literal["US_ACH", "PAYMAN_AGENT"],
    name: str,
    customer_id: Optional[str] = None,
    account_holder_name: Optional[str] = None,
    account_holder_type: Optional[Literal["individual", "business"]] = None,
    account_number: Optional[str] = None,
    routing_number: Optional[str] = None,
    account_type: Optional[Literal["checking", "savings"]] = None,
    payman_agent_id: Optional[str] = None,
    contact_details: Optional[Dict] = None
) -> Dict:
    """
    Create a new payment destination for future USD payments.
    
    Args:
        type: Type of payment destination ("US_ACH" or "PAYMAN_AGENT")
        name: Name for the payment destination
        customer_id: Customer ID who owns this destination (required for US_ACH)
        account_holder_name: Name of the account holder (required for US_ACH)
        account_holder_type: Type of account holder ("individual" or "business") (required for US_ACH)
        account_number: Bank account number (required for US_ACH)
        routing_number: Bank routing number (required for US_ACH)
        account_type: Type of bank account ("checking" or "savings") (required for US_ACH)
        payman_agent_id: The unique ID of the receiving agent (required for PAYMAN_AGENT)
        contact_details: Optional dictionary containing contact information
    
    Returns:
        Dictionary containing the created payee details
    """
    try:
        params = {
            "type": type,
            "name": name,
            "contact_details": contact_details
        }
        
        if type == "US_ACH":
            params.update({
                "customer_id": customer_id,
                "account_holder_name": account_holder_name,
                "account_holder_type": account_holder_type,
                "account_number": account_number,
                "routing_number": routing_number,
                "account_type": account_type
            })
        elif type == "PAYMAN_AGENT":
            params.update({
                "payman_agent_id": payman_agent_id
            })
            
        return client.payments.create_payee(params)
    except Exception as e:
        return {"error": f"Failed to create payee: {str(e)}"}

def initiate_customer_deposit(
    amount_decimal: float,
    customer_id: str,
    customer_email: Optional[str] = None,
    customer_name: Optional[str] = None,
    fee_mode: Optional[Literal["INCLUDED_IN_AMOUNT", "ADD_TO_AMOUNT"]] = None,
    memo: Optional[str] = None,
    wallet_id: Optional[str] = None
) -> Dict:
    """
    Generate a checkout link for customer USD deposits.
    
    Args:
        amount_decimal: Amount to deposit in USD (e.g. 10.00 for $10.00)
        customer_id: ID of the customer to deposit funds for
        customer_email: Optional email address of the customer
        customer_name: Optional name of the customer
        fee_mode: How to handle processing fees ("INCLUDED_IN_AMOUNT" or "ADD_TO_AMOUNT")
        memo: Optional memo for the transaction
        wallet_id: Optional ID of specific wallet to deposit to
    
    Returns:
        Dictionary containing the checkout URL
    """
    try:
        response = client.payments.initiate_customer_deposit(
            amount_decimal=amount_decimal,
            customer_id=customer_id,
            customer_email=customer_email,
            customer_name=customer_name,
            fee_mode=fee_mode,
            memo=memo,
            wallet_id=wallet_id
        )
        return response
    except Exception as e:
        return {"error": f"Failed to generate deposit link: {str(e)}"}

def get_customer_balance(
    customer_id: str,
    currency: Literal["USD"] = "USD"
) -> Dict:
    """
    Check customer's available USD balance.
    
    Args:
        customer_id: ID of the customer to check balance for
        currency: Currency code (always USD)
    
    Returns:
        Dictionary containing balance information
    """
    try:
        response = client.balances.get_customer_balance(customer_id, currency)
        return {
            "spendable_balance": response,
            "currency": currency,
            "customer_id": customer_id
        }
    except Exception as e:
        return {"error": f"Failed to get customer balance: {str(e)}"}

def get_spendable_balance(
    currency: Literal["USD"] = "USD"
) -> Dict:
    """
    Check agent's available USD balance.
    
    Args:
        currency: Currency code (always USD)
    
    Returns:
        Dictionary containing balance information
    """
    try:
        response = client.balances.get_spendable_balance(currency)
        return {
            "spendable_balance": response,
            "currency": currency
        }
    except Exception as e:
        return {"error": f"Failed to get spendable balance: {str(e)}"}