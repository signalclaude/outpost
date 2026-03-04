"""Microsoft To Do (Tasks) API operations."""

from outpost.api.client import GraphClient
from outpost.utils.dates import to_graph_date


# Graph API priority mapping
PRIORITY_MAP = {
    "low": "low",
    "normal": "normal",
    "high": "high",
}


def get_task_lists(client: GraphClient) -> list[dict]:
    """Get all task lists for the current user."""
    return client.get_all_pages("/me/todo/lists")


def find_task_list_id(client: GraphClient, name: str | None = None) -> str:
    """Find a task list ID by name, or return the default list ID.

    If name is None, returns the first list (usually "Tasks" default list).
    Raises ValueError if the named list is not found.
    """
    lists = get_task_lists(client)
    if not lists:
        raise ValueError("No task lists found. Is your account set up?")

    if name is None:
        # Return the default list (wellknownListName == "defaultList" or first)
        for lst in lists:
            if lst.get("wellknownListName") == "defaultList":
                return lst["id"]
        return lists[0]["id"]

    # Search by display name (case-insensitive)
    for lst in lists:
        if lst.get("displayName", "").lower() == name.lower():
            return lst["id"]

    available = [lst.get("displayName", "") for lst in lists]
    raise ValueError(f"Task list {name!r} not found. Available lists: {', '.join(available)}")


def add_task(
    client: GraphClient,
    title: str,
    due_date: str | None = None,
    list_name: str | None = None,
    priority: str = "normal",
) -> dict:
    """Create a new task.

    Args:
        client: GraphClient instance
        title: Task title
        due_date: ISO date string for due date (optional)
        list_name: Task list name (optional, uses default list)
        priority: "low", "normal", or "high"

    Returns: Created task dict from Graph API
    """
    list_id = find_task_list_id(client, list_name)

    body: dict = {
        "title": title,
        "importance": PRIORITY_MAP.get(priority, "normal"),
    }

    if due_date:
        body["dueDateTime"] = {
            "dateTime": f"{due_date}T00:00:00",
            "timeZone": "UTC",
        }

    return client.post(f"/me/todo/lists/{list_id}/tasks", json=body)


def list_tasks(
    client: GraphClient,
    due_filter: str | None = None,
    list_name: str | None = None,
) -> list[dict]:
    """List tasks, optionally filtered by due date and list.

    Args:
        client: GraphClient instance
        due_filter: ISO date string to filter tasks due on this date
        list_name: Task list name (optional, uses default list)

    Returns: List of task dicts
    """
    list_id = find_task_list_id(client, list_name)

    params = {}
    if due_filter:
        params["$filter"] = (
            f"dueDateTime/dateTime ge '{due_filter}T00:00:00' "
            f"and dueDateTime/dateTime lt '{due_filter}T23:59:59'"
        )

    return client.get_all_pages(f"/me/todo/lists/{list_id}/tasks", params=params or None)


def update_task(
    client: GraphClient,
    task_id: str,
    list_name: str | None = None,
    title: str | None = None,
    due_date: str | None = None,
    priority: str | None = None,
) -> dict:
    """Update an existing task. Only provided fields are changed."""
    list_id = find_task_list_id(client, list_name)
    body: dict = {}
    if title is not None:
        body["title"] = title
    if due_date is not None:
        body["dueDateTime"] = {
            "dateTime": f"{due_date}T00:00:00",
            "timeZone": "UTC",
        }
    if priority is not None:
        body["importance"] = PRIORITY_MAP.get(priority, "normal")
    return client.patch(f"/me/todo/lists/{list_id}/tasks/{task_id}", json=body)


def complete_task(
    client: GraphClient,
    task_id: str,
    list_name: str | None = None,
) -> dict:
    """Mark a task as completed."""
    list_id = find_task_list_id(client, list_name)
    return client.patch(
        f"/me/todo/lists/{list_id}/tasks/{task_id}",
        json={"status": "completed"},
    )


def delete_task(
    client: GraphClient,
    task_id: str,
    list_name: str | None = None,
) -> dict:
    """Delete a task."""
    list_id = find_task_list_id(client, list_name)
    return client.delete(f"/me/todo/lists/{list_id}/tasks/{task_id}")


def create_task_list(client: GraphClient, display_name: str) -> dict:
    """Create a new task list."""
    return client.post("/me/todo/lists", json={"displayName": display_name})


def delete_task_list(client: GraphClient, list_id: str) -> dict:
    """Delete a task list."""
    return client.delete(f"/me/todo/lists/{list_id}")
