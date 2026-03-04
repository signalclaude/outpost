"""Microsoft Teams API operations."""

import httpx

from outpost.api.client import GraphClient


def list_teams(client: GraphClient) -> list[dict]:
    """List teams the current user has joined."""
    result = client.get("/me/joinedTeams")
    return result.get("value", [])


def list_channels(client: GraphClient, team_id: str) -> list[dict]:
    """List channels in a team."""
    result = client.get(f"/teams/{team_id}/channels")
    return result.get("value", [])


def list_messages(
    client: GraphClient,
    team_id: str,
    channel_id: str,
    top: int = 25,
) -> list[dict]:
    """List messages in a Teams channel.

    Args:
        client: GraphClient instance
        team_id: Team ID
        channel_id: Channel ID
        top: Maximum number of messages to return
    """
    params = {"$top": str(top)}
    result = client.get(
        f"/teams/{team_id}/channels/{channel_id}/messages",
        params=params,
    )
    return result.get("value", [])


def send_message(
    client: GraphClient,
    team_id: str,
    channel_id: str,
    content: str,
) -> dict:
    """Send a message to a Teams channel.

    Args:
        client: GraphClient instance
        team_id: Team ID
        channel_id: Channel ID
        content: Message content (HTML supported)
    """
    return client.post(
        f"/teams/{team_id}/channels/{channel_id}/messages",
        json={"body": {"content": content}},
    )


def get_channel_files_folder(
    client: GraphClient,
    team_id: str,
    channel_id: str,
) -> dict:
    """Get the SharePoint files folder for a channel.

    Returns a driveItem with id and parentReference.driveId needed for file operations.
    """
    return client.get(f"/teams/{team_id}/channels/{channel_id}/filesFolder")


def list_files(
    client: GraphClient,
    drive_id: str,
    item_id: str,
) -> list[dict]:
    """List children of a drive item (files and folders).

    Args:
        client: GraphClient instance
        drive_id: Drive ID from the filesFolder response
        item_id: Item ID of the folder
    """
    result = client.get(f"/drives/{drive_id}/items/{item_id}/children")
    return result.get("value", [])


def download_file(
    client: GraphClient,
    drive_id: str,
    item_id: str,
) -> tuple[str, bytes]:
    """Download a file from OneDrive/SharePoint.

    Uses the pre-authenticated @microsoft.graph.downloadUrl from the driveItem
    response — no Bearer token needed for the actual download.

    Returns: (filename, content_bytes)
    """
    item = client.get(f"/drives/{drive_id}/items/{item_id}")
    filename = item.get("name", "download")
    download_url = item.get("@microsoft.graph.downloadUrl")
    if not download_url:
        raise ValueError(f"No download URL available for item {item_id}")
    response = httpx.get(download_url)
    response.raise_for_status()
    return filename, response.content


def upload_file(
    client: GraphClient,
    drive_id: str,
    parent_item_id: str,
    filename: str,
    content: bytes,
) -> dict:
    """Upload a file to OneDrive/SharePoint (simple upload, <4MB).

    Args:
        client: GraphClient instance
        drive_id: Drive ID
        parent_item_id: Parent folder item ID
        filename: Name for the uploaded file
        content: File content as bytes

    Returns: The created/updated driveItem dict
    """
    path = f"/drives/{drive_id}/items/{parent_item_id}:/{filename}:/content"
    return client.put(path, content)
