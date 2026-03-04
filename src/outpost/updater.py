"""Version check and self-update for outpost CLI."""

import json
import subprocess
import sys
import time
from pathlib import Path

import httpx

from outpost import __version__
from outpost.config import get_config_dir

GITHUB_REPO = "signalclaude/outpost"
CACHE_FILE = "update_check.json"
CACHE_TTL = 86400  # 24 hours


def fetch_latest_release() -> dict | None:
    """Fetch the latest release info from GitHub.

    Returns dict with 'latest_version' and 'download_url' keys, or None on failure.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        resp = httpx.get(url, timeout=5.0, follow_redirects=True)
        resp.raise_for_status()
    except (httpx.HTTPError, httpx.TimeoutException):
        return None

    data = resp.json()
    tag = data.get("tag_name", "")
    version_str = tag.lstrip("v")
    if not version_str:
        return None

    # Find wheel asset
    download_url = None
    for asset in data.get("assets", []):
        if asset["name"].endswith(".whl"):
            download_url = asset["browser_download_url"]
            break

    # Fallback to git+https install URL
    if not download_url:
        download_url = f"git+https://github.com/{GITHUB_REPO}.git@{tag}"

    return {"latest_version": version_str, "download_url": download_url}


def _cache_path() -> Path:
    return get_config_dir() / CACHE_FILE


def _read_cache() -> dict | None:
    """Read cached update check result. Returns None if missing or expired."""
    path = _cache_path()
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        if time.time() - data.get("checked_at", 0) > CACHE_TTL:
            return None
        return data
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def _write_cache(info: dict) -> None:
    """Write update check result to cache."""
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {**info, "checked_at": time.time()}
    with open(path, "w") as f:
        json.dump(data, f)


def check_for_update(force: bool = False) -> dict | None:
    """Check if a newer version is available.

    Returns dict with 'latest_version' and 'download_url' if update available,
    or None if up-to-date or check failed.
    """
    from packaging.version import Version

    if not force:
        cached = _read_cache()
        if cached:
            try:
                if Version(cached["latest_version"]) > Version(__version__):
                    return cached
            except Exception:
                pass
            return None

    info = fetch_latest_release()
    if info is None:
        return None

    _write_cache(info)

    try:
        if Version(info["latest_version"]) > Version(__version__):
            return info
    except Exception:
        return None

    return None


def perform_update(download_url: str) -> bool:
    """Download and install the update via pip.

    Returns True on success, False on failure.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", download_url],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False
