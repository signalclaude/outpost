"""Authentication module for outpost CLI (MSAL device code flow)."""

import sys

import msal
from rich.console import Console

from outpost.config import DEFAULT_CLIENT_ID, AUTHORITY, get_active_scopes, get_config_dir, get_profile

stderr = Console(stderr=True)

# Cache MSAL app instances per profile
_app_instances: dict[str | None, msal.PublicClientApplication] = {}


def _get_cache() -> msal.SerializableTokenCache:
    """Create a persistent token cache backed by a file in the config dir.

    Uses msal-extensions for OS-level encryption where available
    (DPAPI on Windows, Keychain on macOS, libsecret on Linux),
    falling back to plain file.
    """
    cache_path = str(get_config_dir() / "token_cache.bin")
    get_config_dir().mkdir(parents=True, exist_ok=True)

    try:
        from msal_extensions import (
            FilePersistenceWithDataProtection,
            KeychainPersistence,
            LibsecretPersistence,
            PersistedTokenCache,
        )
        import platform

        system = platform.system()
        if system == "Windows":
            persistence = FilePersistenceWithDataProtection(cache_path)
        elif system == "Darwin":
            persistence = KeychainPersistence(cache_path, "OutpostCLI", "outpost_token_cache")
        else:
            persistence = LibsecretPersistence(
                cache_path,
                schema_name="org.outpost.tokencache",
                attributes={"app": "outpost"},
            )
        return PersistedTokenCache(persistence)
    except Exception:
        # Fallback: plain file-backed cache (no OS encryption)
        from msal_extensions import FilePersistence, PersistedTokenCache

        persistence = FilePersistence(cache_path)
        return PersistedTokenCache(persistence)


def _get_msal_app() -> msal.PublicClientApplication | None:
    """Get or create a cached MSAL PublicClientApplication for the current profile."""
    if not DEFAULT_CLIENT_ID:
        return None
    profile = get_profile()
    if profile not in _app_instances:
        _app_instances[profile] = msal.PublicClientApplication(
            DEFAULT_CLIENT_ID,
            authority=AUTHORITY,
            token_cache=_get_cache(),
        )
    return _app_instances[profile]


def login_interactive(scopes: list[str] | None = None) -> bool:
    """Run the device code flow for interactive login.

    Args:
        scopes: OAuth scopes to request. Defaults to get_active_scopes().

    Returns True on success, False on failure.
    """
    app = _get_msal_app()
    if app is None:
        stderr.print(
            "[yellow]Azure AD app not configured yet.[/yellow]\n"
            "Set DEFAULT_CLIENT_ID in outpost/config.py after registering your Azure AD app."
        )
        return False

    if scopes is None:
        scopes = get_active_scopes()
    flow = app.initiate_device_flow(scopes=scopes)
    if "user_code" not in flow:
        stderr.print(f"[red]Failed to start device flow:[/red] {flow.get('error_description', 'unknown error')}")
        return False

    stderr.print(f"\nTo sign in, visit: [bold]{flow['verification_uri']}[/bold]")
    stderr.print(f"Enter code: [bold]{flow['user_code']}[/bold]\n")
    stderr.print("Waiting for you to complete sign-in in your browser...")

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        stderr.print("[green]Successfully logged in![/green]")
        return True
    else:
        stderr.print(f"[red]Login failed:[/red] {result.get('error_description', 'unknown error')}")
        return False


def get_token() -> str | None:
    """Get an access token silently from cache/refresh token. Returns None if not available."""
    app = _get_msal_app()
    if app is None:
        return None

    accounts = app.get_accounts()
    if not accounts:
        return None

    result = app.acquire_token_silent(get_active_scopes(), account=accounts[0])
    if result and "access_token" in result:
        return result["access_token"]
    return None


def require_token() -> str:
    """Get an access token or exit with a helpful error message."""
    token = get_token()
    if token is None:
        stderr.print("[red]Not logged in.[/red] Run [bold]outpost setup[/bold] to connect your Microsoft account.")
        sys.exit(1)
    return token


def get_auth_status() -> dict:
    """Return current auth status as a dict."""
    app = _get_msal_app()
    if app is None:
        return {"logged_in": False, "username": None, "message": "Azure AD app not configured"}

    accounts = app.get_accounts()
    if accounts:
        return {
            "logged_in": True,
            "username": accounts[0].get("username", "unknown"),
        }
    return {"logged_in": False, "username": None}
