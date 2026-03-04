"""Outpost — a CLI for Microsoft Outlook via Microsoft Graph API."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("outpost-cli")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"
