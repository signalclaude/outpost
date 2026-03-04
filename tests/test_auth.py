"""Tests for outpost auth module."""

from unittest.mock import patch, MagicMock

import pytest

from outpost.auth import get_auth_status, get_token, login_interactive, require_token


class TestGetAuthStatus:
    def test_no_client_id(self):
        with patch("outpost.auth.DEFAULT_CLIENT_ID", ""), \
             patch("outpost.auth._app_instance", None):
            status = get_auth_status()
        assert status["logged_in"] is False
        assert status["username"] is None

    def test_no_accounts(self):
        mock_app = MagicMock()
        mock_app.get_accounts.return_value = []
        with patch("outpost.auth._get_msal_app", return_value=mock_app):
            status = get_auth_status()
        assert status["logged_in"] is False

    def test_with_account(self):
        mock_app = MagicMock()
        mock_app.get_accounts.return_value = [{"username": "user@example.com"}]
        with patch("outpost.auth._get_msal_app", return_value=mock_app):
            status = get_auth_status()
        assert status["logged_in"] is True
        assert status["username"] == "user@example.com"


class TestGetToken:
    def test_no_client_id_returns_none(self):
        with patch("outpost.auth.DEFAULT_CLIENT_ID", ""):
            assert get_token() is None

    def test_no_accounts_returns_none(self):
        mock_app = MagicMock()
        mock_app.get_accounts.return_value = []
        with patch("outpost.auth._get_msal_app", return_value=mock_app):
            assert get_token() is None

    def test_token_from_cache(self):
        mock_app = MagicMock()
        mock_app.get_accounts.return_value = [{"username": "user@example.com"}]
        mock_app.acquire_token_silent.return_value = {"access_token": "my-token"}
        with patch("outpost.auth._get_msal_app", return_value=mock_app):
            assert get_token() == "my-token"


class TestRequireToken:
    def test_exits_when_no_token(self):
        with patch("outpost.auth.get_token", return_value=None):
            with pytest.raises(SystemExit):
                require_token()

    def test_returns_token(self):
        with patch("outpost.auth.get_token", return_value="my-token"):
            assert require_token() == "my-token"


class TestLoginInteractive:
    def test_no_client_id(self):
        with patch("outpost.auth.DEFAULT_CLIENT_ID", ""):
            result = login_interactive()
        assert result is False

    def test_device_flow_success(self):
        mock_app = MagicMock()
        mock_app.initiate_device_flow.return_value = {
            "user_code": "ABC123",
            "verification_uri": "https://microsoft.com/devicelogin",
        }
        mock_app.acquire_token_by_device_flow.return_value = {"access_token": "token"}
        with patch("outpost.auth._get_msal_app", return_value=mock_app):
            result = login_interactive()
        assert result is True

    def test_device_flow_failure(self):
        mock_app = MagicMock()
        mock_app.initiate_device_flow.return_value = {
            "user_code": "ABC123",
            "verification_uri": "https://microsoft.com/devicelogin",
        }
        mock_app.acquire_token_by_device_flow.return_value = {
            "error_description": "user cancelled"
        }
        with patch("outpost.auth._get_msal_app", return_value=mock_app):
            result = login_interactive()
        assert result is False
