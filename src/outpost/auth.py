"""Authentication module for outpost CLI (MSAL interactive + device code flow)."""

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


def login_browser(scopes: list[str] | None = None) -> bool:
    """Interactive login via the system browser (auth code + PKCE).

    Opens the default browser and captures the redirect on a loopback port.
    Unlike the device code flow, this is NOT blocked by Conditional Access
    policies that restrict device-code authentication (AADSTS error: "an
    authentication flow that is restricted by your admin"). Prefer this flow.

    Requires the Azure app registration to list ``http://localhost`` as a
    redirect URI under "Mobile and desktop applications" (public client).

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

    stderr.print("\n[bold]Opening your browser to sign in...[/bold]")
    stderr.print("[dim]If it doesn't open, check for a browser window or tab.[/dim]")

    result = app.acquire_token_interactive(scopes=scopes)
    if "access_token" in result:
        stderr.print("[green]Successfully logged in![/green]")
        return True

    stderr.print(f"[red]Login failed:[/red] {result.get('error_description', 'unknown error')}")
    return False


def login_interactive(scopes: list[str] | None = None) -> bool:
    """Run the device code flow for interactive login.

    Note: many tenants block this flow via Conditional Access. Prefer
    ``login_browser`` unless a headless/no-browser environment requires
    device code.

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
    """Return current auth status as a dict.

    Validates the cached token rather than just checking for a cached account.
    A cached account whose refresh token has expired (90-day inactivity) or
    no longer covers the active scopes is reported as not logged in, with a
    message telling the user to re-authenticate.
    """
    app = _get_msal_app()
    if app is None:
        return {"logged_in": False, "username": None, "message": "Azure AD app not configured"}

    accounts = app.get_accounts()
    if not accounts:
        return {"logged_in": False, "username": None, "message": "No account signed in"}

    username = accounts[0].get("username", "unknown")
    result = app.acquire_token_silent_with_error(get_active_scopes(), account=accounts[0])
    if result and "access_token" in result:
        return {"logged_in": True, "username": username}

    # Account is cached but the token can't be silently obtained — expired
    # refresh token or scope change. Surface the underlying reason.
    detail = result.get("error_description", "session expired") if result else "session expired"
    first_line = detail.splitlines()[0] if detail else "session expired"
    return {
        "logged_in": False,
        "username": username,
        "message": f"Session expired for {username} — run 'outpost auth login' to re-authenticate.",
        "detail": first_line,
    }
