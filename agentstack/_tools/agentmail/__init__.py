from agentmail import AgentMail
from typing import Optional, List


client = AgentMail()


def list_inboxes(limit: Optional[int] = None, last_key: Optional[str] = None):
    """
    List inboxes.

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


def list_threads(
    inbox_id: str, limit: Optional[int] = None, last_key: Optional[str] = None
):
    """
    List threads in an inbox.

    Args:
        inbox_id: The ID of the inbox to list threads for.
        limit: The maximum number of threads to return.
        last_key: The last key returned from the previous page.

    Returns:
        A list of threads.
    """
    return client.threads.list(inbox_id=inbox_id, limit=limit, last_key=last_key)


def get_thread(inbox_id: str, thread_id: str):
    """
    Get a thread by ID.

    Args:
        inbox_id: The ID of the inbox to get the thread for.
        thread_id: The ID of the thread to get.

    Returns:
        A thread.
    """
    return client.threads.get(inbox_id=inbox_id, thread_id=thread_id)


def list_messages(
    inbox_id: str, limit: Optional[int] = None, last_key: Optional[str] = None
):
    """
    List messages in an inbox.

    Args:
        inbox_id: The ID of the inbox to list messages for.
        limit: The maximum number of messages to return.
        last_key: The last key returned from the previous page.

    Returns:
        A list of messages.
    """
    return client.messages.list(inbox_id=inbox_id, limit=limit, last_key=last_key)


def get_message(inbox_id: str, message_id: str):
    """
    Get a message by ID.

    Args:
        inbox_id: The ID of the inbox to get the message for.
        message_id: The ID of the message to get.

    Returns:
        A message.
    """
    return client.messages.get(inbox_id=inbox_id, message_id=message_id)


def get_attachment(inbox_id: str, message_id: str, attachment_id: str):
    """
    Get an attachment by message ID and attachment ID.

    Args:
        inbox_id: The ID of the inbox to get the attachment for.
        message_id: The ID of the message to get the attachment for.
        attachment_id: The ID of the attachment to get.

    Returns:
        An attachment.
    """
    return client.messages.get_attachment(
        inbox_id=inbox_id, message_id=message_id, attachment_id=attachment_id
    )


def send_message(
    inbox_id: str,
    to: List[str],
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    subject: Optional[str] = None,
    text: Optional[str] = None,
    html: Optional[str] = None,
):
    """
    Send a message.

    Args:
        inbox_id: The ID of the inbox to send the message from.
        to: The list of recipients.
        cc: The list of CC recipients.
        bcc: The list of BCC recipients.
        subject: The subject of the message.
        text: The plain text body of the message.
        html: The HTML body of the message.

    Returns:
        A message.
    """
    return client.messages.send(
        inbox_id=inbox_id, to=to, cc=cc, bcc=bcc, subject=subject, text=text, html=html
    )


def reply_to_message(
    inbox_id: str,
    message_id: str,
    text: Optional[str] = None,
    html: Optional[str] = None,
):
    """
    Reply to a message.

    Args:
        inbox_id: The ID of the inbox to reply to the message in.
        message_id: The ID of the message to reply to.
        text: The plain text body of the reply.
        html: The HTML body of the reply.

    Returns:
        A message.
    """
    return client.messages.reply(
        inbox_id=inbox_id, message_id=message_id, text=text, html=html
    )
