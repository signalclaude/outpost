"""Tests for outpost.updater — version check and self-update."""

import json
import time
from unittest.mock import patch, MagicMock

import httpx
import pytest
import respx

from outpost.updater import (
    fetch_latest_release,
    _read_cache,
    _write_cache,
    _cache_path,
    check_for_update,
    perform_update,
    GITHUB_REPO,
    CACHE_TTL,
)


RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

RELEASE_WITH_WHEEL = {
    "tag_name": "v0.2.0",
    "assets": [
        {
            "name": "outpost_cli-0.2.0-py3-none-any.whl",
            "browser_download_url": "https://github.com/signalclaude/outpost/releases/download/v0.2.0/outpost_cli-0.2.0-py3-none-any.whl",
        }
    ],
}

RELEASE_NO_WHEEL = {
    "tag_name": "v0.2.0",
    "assets": [
        {"name": "outpost-0.2.0.tar.gz", "browser_download_url": "https://example.com/outpost-0.2.0.tar.gz"}
    ],
}

RELEASE_NO_ASSETS = {
    "tag_name": "v0.2.0",
    "assets": [],
}


# ── fetch_latest_release ────────────────────────────────────────────────────


@respx.mock
def test_fetch_latest_release_with_wheel():
    respx.get(RELEASES_URL).mock(return_value=httpx.Response(200, json=RELEASE_WITH_WHEEL))
    result = fetch_latest_release()
    assert result is not None
    assert result["latest_version"] == "0.2.0"
    assert result["download_url"].endswith(".whl")


@respx.mock
def test_fetch_latest_release_no_wheel_falls_back_to_git():
    respx.get(RELEASES_URL).mock(return_value=httpx.Response(200, json=RELEASE_NO_WHEEL))
    result = fetch_latest_release()
    assert result is not None
    assert result["latest_version"] == "0.2.0"
    assert result["download_url"].startswith("git+https://")
    assert "v0.2.0" in result["download_url"]


@respx.mock
def test_fetch_latest_release_no_assets_falls_back_to_git():
    respx.get(RELEASES_URL).mock(return_value=httpx.Response(200, json=RELEASE_NO_ASSETS))
    result = fetch_latest_release()
    assert result is not None
    assert result["download_url"].startswith("git+https://")


@respx.mock
def test_fetch_latest_release_github_error():
    respx.get(RELEASES_URL).mock(return_value=httpx.Response(404))
    result = fetch_latest_release()
    assert result is None


@respx.mock
def test_fetch_latest_release_network_error():
    respx.get(RELEASES_URL).mock(side_effect=httpx.ConnectError("connection failed"))
    result = fetch_latest_release()
    assert result is None


# ── Cache ────────────────────────────────────────────────────────────────────


def test_write_and_read_cache(tmp_path):
    with patch("outpost.updater._cache_path", return_value=tmp_path / "update_check.json"):
        info = {"latest_version": "0.2.0", "download_url": "https://example.com/wheel.whl"}
        _write_cache(info)
        result = _read_cache()
        assert result is not None
        assert result["latest_version"] == "0.2.0"


def test_cache_expired(tmp_path):
    cache_file = tmp_path / "update_check.json"
    with patch("outpost.updater._cache_path", return_value=cache_file):
        data = {"latest_version": "0.2.0", "download_url": "https://example.com", "checked_at": time.time() - CACHE_TTL - 1}
        with open(cache_file, "w") as f:
            json.dump(data, f)
        result = _read_cache()
        assert result is None


def test_cache_missing(tmp_path):
    with patch("outpost.updater._cache_path", return_value=tmp_path / "nonexistent.json"):
        result = _read_cache()
        assert result is None


def test_cache_corrupt(tmp_path):
    cache_file = tmp_path / "update_check.json"
    cache_file.write_text("not json{{{")
    with patch("outpost.updater._cache_path", return_value=cache_file):
        result = _read_cache()
        assert result is None


# ── check_for_update ─────────────────────────────────────────────────────────


@respx.mock
def test_check_for_update_available(tmp_path):
    respx.get(RELEASES_URL).mock(return_value=httpx.Response(200, json=RELEASE_WITH_WHEEL))
    with patch("outpost.updater.__version__", "0.1.0"), \
         patch("outpost.updater._cache_path", return_value=tmp_path / "update_check.json"):
        result = check_for_update(force=True)
        assert result is not None
        assert result["latest_version"] == "0.2.0"


@respx.mock
def test_check_for_update_up_to_date(tmp_path):
    release = {**RELEASE_WITH_WHEEL, "tag_name": "v0.1.0"}
    respx.get(RELEASES_URL).mock(return_value=httpx.Response(200, json=release))
    with patch("outpost.updater.__version__", "0.1.0"), \
         patch("outpost.updater._cache_path", return_value=tmp_path / "update_check.json"):
        result = check_for_update(force=True)
        assert result is None


def test_check_for_update_uses_cache(tmp_path):
    cache_file = tmp_path / "update_check.json"
    data = {"latest_version": "0.3.0", "download_url": "https://example.com/wheel.whl", "checked_at": time.time()}
    with open(cache_file, "w") as f:
        json.dump(data, f)
    with patch("outpost.updater.__version__", "0.1.0"), \
         patch("outpost.updater._cache_path", return_value=cache_file):
        result = check_for_update(force=False)
        assert result is not None
        assert result["latest_version"] == "0.3.0"


def test_check_for_update_cache_up_to_date(tmp_path):
    cache_file = tmp_path / "update_check.json"
    data = {"latest_version": "0.1.0", "download_url": "https://example.com/wheel.whl", "checked_at": time.time()}
    with open(cache_file, "w") as f:
        json.dump(data, f)
    with patch("outpost.updater.__version__", "0.1.0"), \
         patch("outpost.updater._cache_path", return_value=cache_file):
        result = check_for_update(force=False)
        assert result is None


# ── perform_update ───────────────────────────────────────────────────────────


def test_perform_update_success():
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        assert perform_update("https://example.com/wheel.whl") is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "pip" in args[2]
        assert "https://example.com/wheel.whl" in args


def test_perform_update_failure():
    mock_result = MagicMock()
    mock_result.returncode = 1
    with patch("subprocess.run", return_value=mock_result):
        assert perform_update("https://example.com/wheel.whl") is False


def test_perform_update_git_fallback():
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        url = f"git+https://github.com/{GITHUB_REPO}.git@v0.2.0"
        assert perform_update(url) is True
        args = mock_run.call_args[0][0]
        assert url in args


def test_perform_update_exception():
    with patch("subprocess.run", side_effect=OSError("spawn failed")):
        assert perform_update("https://example.com/wheel.whl") is False
