"""Microsoft Outlook Contacts API operations (read-only)."""

from outpost.api.client import GraphClient


def list_contacts(client: GraphClient, top: int = 50) -> list[dict]:
    """List contacts.

    Args:
        client: GraphClient instance
        top: Maximum number of contacts to return
    """
    params = {
        "$top": str(top),
        "$orderby": "displayName",
        "$select": "id,displayName,emailAddresses,businessPhones,mobilePhone",
    }
    result = client.get("/me/contacts", params=params)
    return result.get("value", [])


def search_contacts(client: GraphClient, query: str, top: int = 25) -> list[dict]:
    """Search contacts by name or email.

    Args:
        client: GraphClient instance
        query: Search query
        top: Maximum number of results
    """
    params = {
        "$search": f'"{query}"',
        "$top": str(top),
        "$select": "id,displayName,emailAddresses,businessPhones,mobilePhone",
    }
    result = client.get(
        "/me/contacts",
        params=params,
        headers={"ConsistencyLevel": "eventual"},
    )
    return result.get("value", [])
