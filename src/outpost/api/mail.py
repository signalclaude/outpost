"""Microsoft Outlook Mail API operations."""

import base64
from pathlib import Path

from outpost.api.client import GraphClient


def list_messages(
    client: GraphClient,
    folder: str = "inbox",
    top: int = 25,
    unread: bool = False,
) -> list[dict]:
    """List messages in a mail folder.

    Args:
        client: GraphClient instance
        folder: Mail folder (inbox, sentitems, drafts, deleteditems)
        top: Maximum number of messages to return
        unread: If True, show only unread messages
    """
    params: dict = {
        "$top": str(top),
        "$orderby": "receivedDateTime desc",
        "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview",
    }
    if unread:
        params["$filter"] = "isRead eq false"
    result = client.get(f"/me/mailFolders/{folder}/messages", params=params)
    return result.get("value", [])


def get_message(client: GraphClient, message_id: str) -> dict:
    """Get a single message with full body."""
    params = {
        "$select": "id,subject,from,toRecipients,ccRecipients,receivedDateTime,body,isRead,hasAttachments",
    }
    return client.get(f"/me/messages/{message_id}", params=params)


def send_message(
    client: GraphClient,
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
) -> dict:
    """Send an email."""
    to_recipients = [{"emailAddress": {"address": addr}} for addr in to]
    payload: dict = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": to_recipients,
        },
        "saveToSentItems": True,
    }
    if cc:
        payload["message"]["ccRecipients"] = [
            {"emailAddress": {"address": addr}} for addr in cc
        ]
    return client.post("/me/sendMail", json=payload)


def send_message_with_attachments(
    client: GraphClient,
    to: list[str],
    subject: str,
    body: str,
    attachments: list[str],
    cc: list[str] | None = None,
) -> dict:
    """Send an email with file attachments.

    Args:
        client: GraphClient instance
        to: List of recipient email addresses
        subject: Email subject
        body: Email body text
        attachments: List of file paths to attach
        cc: List of CC email addresses (optional)
    """
    to_recipients = [{"emailAddress": {"address": addr}} for addr in to]

    attachment_items = []
    for filepath in attachments:
        path = Path(filepath)
        if not path.exists():
            raise ValueError(f"Attachment file not found: {filepath}")
        content = path.read_bytes()
        attachment_items.append({
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": path.name,
            "contentBytes": base64.b64encode(content).decode("ascii"),
        })

    payload: dict = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": to_recipients,
            "attachments": attachment_items,
        },
        "saveToSentItems": True,
    }
    if cc:
        payload["message"]["ccRecipients"] = [
            {"emailAddress": {"address": addr}} for addr in cc
        ]
    return client.post("/me/sendMail", json=payload)


def reply_message(
    client: GraphClient,
    message_id: str,
    body: str,
) -> dict:
    """Reply to a message."""
    return client.post(
        f"/me/messages/{message_id}/reply",
        json={"comment": body},
    )


def delete_message(client: GraphClient, message_id: str) -> dict:
    """Delete a message."""
    return client.delete(f"/me/messages/{message_id}")


def search_messages(
    client: GraphClient,
    query: str,
    top: int = 25,
) -> list[dict]:
    """Search messages across all folders.

    Args:
        client: GraphClient instance
        query: Search query string
        top: Maximum results to return
    """
    params = {
        "$search": f'"{query}"',
        "$top": str(top),
        "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview",
    }
    result = client.get(
        "/me/messages",
        params=params,
        headers={"ConsistencyLevel": "eventual"},
    )
    return result.get("value", [])


def list_attachments(client: GraphClient, message_id: str) -> list[dict]:
    """List attachments for a message."""
    params = {"$select": "id,name,contentType,size"}
    result = client.get(f"/me/messages/{message_id}/attachments", params=params)
    return result.get("value", [])


def download_attachment(
    client: GraphClient,
    message_id: str,
    attachment_id: str,
) -> tuple[str, bytes]:
    """Download an attachment by ID.

    Returns: (filename, content_bytes)
    """
    result = client.get(f"/me/messages/{message_id}/attachments/{attachment_id}")
    filename = result.get("name", "attachment")
    content = base64.b64decode(result.get("contentBytes", ""))
    return filename, content
