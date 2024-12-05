from dotenv import load_dotenv
import os

from agent_connect.simple_node import SimpleNode
import json

load_dotenv()

# An HTTP and WS service will be started in agent-connect
# It can be an IP address or a domain name
host_domain = os.getenv("HOST_DOMAIN")
# Host port, default is 80
host_port = os.getenv("HOST_PORT")
# WS path, default is /ws
host_ws_path = os.getenv("HOST_WS_PATH")
# Path to store DID document
did_document_path = os.getenv("DID_DOCUMENT_PATH")
# SSL certificate path, if using HTTPS, certificate and key need to be provided
ssl_cert_path = os.getenv("SSL_CERT_PATH")
ssl_key_path = os.getenv("SSL_KEY_PATH")


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
        node.set_did_info(
            did_info["private_key_pem"],
            did_info["did"],
            did_info["did_document_json"]
        )
    else:
        print("Generating new DID information")
        private_key_pem, did, did_document_json = node.generate_did_document()
        node.set_did_info(private_key_pem, did, did_document_json)
        
        # Save DID information
        os.makedirs(os.path.dirname(did_document_path), exist_ok=True)
        with open(did_document_path, "w") as f:
            json.dump({
                "private_key_pem": private_key_pem,
                "did": did,
                "did_document_json": did_document_json
            }, f, indent=2)
        print(f"DID information saved to {did_document_path}")

agent_connect_simple_node = SimpleNode(host_domain, host_port, host_ws_path)
generate_did_info(agent_connect_simple_node, did_document_path)
agent_connect_simple_node.run()

