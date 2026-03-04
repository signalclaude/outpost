"""Configuration management for outpost CLI."""

import json
import platform
import shutil
import tempfile
from pathlib import Path

# Pre-registered Azure AD app client ID
DEFAULT_CLIENT_ID = "03477b6a-a575-413c-b432-aa7bbd123060"

# Microsoft Graph API constants
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
AUTHORITY = "https://login.microsoftonline.com/common"

# Core scopes — always requested
CORE_SCOPES = [
    "Tasks.ReadWrite",
    "Calendars.ReadWrite",
    "Mail.ReadWrite",
    "Mail.Send",
    "Contacts.Read",
    "User.Read",
]

# Optional feature scopes — requested only when the feature is enabled
FEATURE_SCOPES = {
    "teams": [
        "Team.ReadBasic.All",
        "Channel.ReadBasic.All",
        "ChannelMessage.Read.All",
        "ChannelMessage.Send",
        "Files.Read.All",
    ],
}

# Backward compatibility alias
GRAPH_SCOPES = CORE_SCOPES

DEFAULT_CONFIG = {
    "client_id": DEFAULT_CLIENT_ID,
    "default_output": "table",
    "enabled_features": [],
    "timezone": "UTC",
}


def get_active_scopes(config: dict | None = None) -> list[str]:
    """Return the combined scopes for core + all enabled features."""
    if config is None:
        config = load_config()
    scopes = list(CORE_SCOPES)
    for feature in config.get("enabled_features", []):
        scopes.extend(FEATURE_SCOPES.get(feature, []))
    return scopes


def is_feature_enabled(feature: str, config: dict | None = None) -> bool:
    """Check whether an optional feature is enabled in the config."""
    if config is None:
        config = load_config()
    return feature in config.get("enabled_features", [])

# Profile support for multi-account
_current_profile: str | None = None


def set_profile(name: str) -> None:
    """Set the active profile for this session."""
    global _current_profile
    _current_profile = name


def get_profile() -> str | None:
    """Get the active profile name, or None for default."""
    return _current_profile


def get_config_dir() -> Path:
    """Return the platform-appropriate config directory for outpost.

    When a profile is active, returns a profile-specific subdirectory.
    """
    system = platform.system()
    if system == "Windows":
        base = Path.home() / "AppData" / "Local"
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        xdg = Path.home() / ".config"
        base = Path(xdg)
    config_dir = base / "outpost"
    if _current_profile:
        config_dir = config_dir / "profiles" / _current_profile
    return config_dir


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


def get_workspace_dir() -> Path:
    """Return the transient workspace directory for MCP file operations.

    Uses the system temp directory. Profile-aware when a profile is active.
    Creates the directory if it doesn't exist.
    """
    workspace = Path(tempfile.gettempdir()) / "outpost" / "workspace"
    if _current_profile:
        workspace = workspace / "profiles" / _current_profile
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def clean_workspace() -> None:
    """Remove all files from the workspace directory."""
    workspace = get_workspace_dir()
    if workspace.exists():
        shutil.rmtree(workspace)
        workspace.mkdir(parents=True, exist_ok=True)
