from agentmail import AgentMail
from typing import Optional


client = AgentMail()


def list_inboxes(limit: Optional[int] = None, last_key: Optional[str] = None):
    """
    List all inboxes.

    Args:
        limit: The maximum number of inboxes to return.
        last_key: The last key returned from the previous page.

    Returns:
        A list of inboxes.
    """
    return client.inboxes.list(limit=limit, last_key=last_key)


def get_inbox(inbox_id: str):
    """
    Get an inbox by ID.

    Args:
        inbox_id: The ID of the inbox to get.

    Returns:
        An inbox.
    """
    return client.inboxes.get(inbox_id)


def create_inbox(
    username: Optional[str] = None,
    domain: Optional[str] = None,
    display_name: Optional[str] = None,
):
    """
    Create an inbox.

    Args:
        username: The username of the inbox.
        domain: The domain of the inbox.
        display_name: The display name of the inbox.

    Returns:
        An inbox.
    """
    return client.inboxes.create(
        username=username, domain=domain, display_name=display_name
    )
