"""Configuration management for outpost CLI."""

import json
import platform
from pathlib import Path

# Pre-registered Azure AD app client ID
DEFAULT_CLIENT_ID = "03477b6a-a575-413c-b432-aa7bbd123060"

# Microsoft Graph API constants
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPES = [
    "Tasks.ReadWrite",
    "Calendars.ReadWrite",
    "Mail.ReadWrite",
    "Mail.Send",
    "Contacts.Read",
    "User.Read",
]
AUTHORITY = "https://login.microsoftonline.com/common"

DEFAULT_CONFIG = {
    "client_id": DEFAULT_CLIENT_ID,
    "default_output": "table",
}


def get_config_dir() -> Path:
    """Return the platform-appropriate config directory for outpost."""
    system = platform.system()
    if system == "Windows":
        base = Path.home() / "AppData" / "Local"
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        xdg = Path.home() / ".config"
        base = Path(xdg)
    return base / "outpost"


def get_config_path() -> Path:
    """Return the path to the outpost config file."""
    return get_config_dir() / "config.json"


def load_config() -> dict:
    """Load config from disk, returning defaults if file doesn't exist."""
    path = get_config_path()
    if path.exists():
        with open(path) as f:
            stored = json.load(f)
        # Merge with defaults so new keys are always present
        merged = {**DEFAULT_CONFIG, **stored}
        return merged
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    """Save config to disk, creating the directory if needed."""
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(config, f, indent=2)
