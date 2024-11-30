from crewai_tools import tool
from .common import agent_connect_simple_node


@tool("Send Message to Agent by DID")
async def send_message(message: str, destination_did: str) -> bool:
    """
    Send a message through agent-connect node.
    
    Args:
        message: Message content to be sent
        destination_did: DID of the recipient agent
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        await agent_connect_simple_node.send_message(message, destination_did)
        print(f"Successfully sent message: {message}")
        return True
    except Exception as e:
        print(f"Failed to send message: {e}")
        return False

@tool("Receive Message from Agent")
async def receive_message() -> tuple[str, str]:
    """
    Receive message from agent-connect node.
    
    Returns:
        tuple[str, str]: Sender DID and received message content, empty string if no message or error occurred
    """
    try:
        sender_did, message = await agent_connect_simple_node.receive_message()
        if message:
            print(f"Received message from {sender_did}: {message}")
            return sender_did, message
        return "", ""
    except Exception as e:
        print(f"Failed to receive message: {e}")
        return "", ""

