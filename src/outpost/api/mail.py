"""Microsoft Outlook Mail API operations."""

from outpost.api.client import GraphClient


def list_messages(
    client: GraphClient,
    folder: str = "inbox",
    top: int = 25,
) -> list[dict]:
    """List messages in a mail folder.

    Args:
        client: GraphClient instance
        folder: Mail folder (inbox, sentitems, drafts, deleteditems)
        top: Maximum number of messages to return
    """
    params = {
        "$top": str(top),
        "$orderby": "receivedDateTime desc",
        "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview",
    }
    result = client.get(f"/me/mailFolders/{folder}/messages", params=params)
    return result.get("value", [])


def get_message(client: GraphClient, message_id: str) -> dict:
    """Get a single message with full body.

    Args:
        client: GraphClient instance
        message_id: Message ID
    """
    params = {
        "$select": "id,subject,from,toRecipients,ccRecipients,receivedDateTime,body,isRead",
    }
    return client.get(f"/me/messages/{message_id}", params=params)


def send_message(
    client: GraphClient,
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
) -> dict:
    """Send an email.

    Args:
        client: GraphClient instance
        to: List of recipient email addresses
        subject: Email subject
        body: Email body text
        cc: List of CC email addresses (optional)
    """
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


def reply_message(
    client: GraphClient,
    message_id: str,
    body: str,
) -> dict:
    """Reply to a message.

    Args:
        client: GraphClient instance
        message_id: Message ID to reply to
        body: Reply text
    """
    return client.post(
        f"/me/messages/{message_id}/reply",
        json={"comment": body},
    )


def delete_message(client: GraphClient, message_id: str) -> dict:
    """Delete a message.

    Args:
        client: GraphClient instance
        message_id: Message ID to delete
    """
    return client.delete(f"/me/messages/{message_id}")
