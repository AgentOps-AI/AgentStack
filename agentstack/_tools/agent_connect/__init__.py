import os
import json
from agent_connect.simple_node import SimpleNode


# An HTTP and WS service will be started in agent-connect
# It can be an IP address or a domain name
host_domain = os.getenv("AGENT_CONNECT_HOST_DOMAIN")
# Host port, default is 80
host_port = os.getenv("AGENT_CONNECT_HOST_PORT")
# WS path, default is /ws
host_ws_path = os.getenv("AGENT_CONNECT_HOST_WS_PATH")
# Path to store DID document
did_document_path = os.getenv("AGENT_CONNECT_DID_DOCUMENT_PATH")
# SSL certificate path, if using HTTPS, certificate and key need to be provided
ssl_cert_path = os.getenv("AGENT_CONNECT_SSL_CERT_PATH")
ssl_key_path = os.getenv("AGENT_CONNECT_SSL_KEY_PATH")

if not host_domain:
    raise Exception(
        "Host domain has not been provided.\n"
        "Did you set the AGENT_CONNECT_HOST_DOMAIN in you project's .env file?"
    )

if not did_document_path:
    raise Exception(
        "DID document path has not been provided.\n"
        "Did you set the AGENT_CONNECT_DID_DOCUMENT_PATH in you project's .env file?"
    )


def generate_did_info(node: SimpleNode, did_document_path: str) -> None:
    """
    Generate or load DID information for a node.

    Args:
        node: SimpleNode instance
        did_document_path: Path to store/load DID document
    """
    if os.path.exists(did_document_path):
        print(f"Loading existing DID information from {did_document_path}")
        with open(did_document_path, "r") as f:
            did_info = json.load(f)
        node.set_did_info(did_info["private_key_pem"], did_info["did"], did_info["did_document_json"])
    else:
        print("Generating new DID information")
        private_key_pem, did, did_document_json = node.generate_did_document()
        node.set_did_info(private_key_pem, did, did_document_json)

        # Save DID information
        if os.path.dirname(did_document_path):  # allow saving to current directory
            os.makedirs(os.path.dirname(did_document_path), exist_ok=True)
        with open(did_document_path, "w") as f:
            json.dump(
                {"private_key_pem": private_key_pem, "did": did, "did_document_json": did_document_json},
                f,
                indent=2,
            )
        print(f"DID information saved to {did_document_path}")


agent_connect_simple_node = SimpleNode(host_domain, host_port, host_ws_path)
generate_did_info(agent_connect_simple_node, did_document_path)
agent_connect_simple_node.run()


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
