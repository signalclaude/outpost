# Changelog

All notable changes to Outpost are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/).

## [0.1.2] — 2026-03-04

### Added
- `outpost --version` / `-V` flag to display current version
- `outpost update` command — check for new releases and self-update from GitHub
  - `--check` flag to only check without installing
  - `--force` flag to bypass 24h cache and check GitHub now
  - Auto-check notice on stderr when a newer version is available (interactive terminals only)
- `__version__` now reads from `importlib.metadata` (single source of truth: `pyproject.toml`)
- Remote MCP access via SSE or streamable-http transport with bearer token auth (#5)
  - `--host` flag on `outpost mcp serve` (use `0.0.0.0` for LAN access)
  - API key auto-generated on first use, stored in config
  - Bearer token enforced on all network transport requests
  - `outpost mcp key` — display current API key
  - `outpost mcp key --regenerate` — rotate the API key
  - `streamable-http` transport option (newer MCP spec)
- Teams 1:1 and group chat support (#4)
  - `outpost teams chats` — list recent chats (1:1, group, meeting)
  - `outpost teams chat-messages <id>` — read messages from a chat
  - `outpost teams chat-send <id> --body "..."` — send a message to a chat
  - 3 new MCP tools: `teams_chats`, `teams_chat_messages`, `teams_chat_send` (39 tools total)
  - New scopes: `Chat.Read`, `ChatMessage.Send` (re-run `outpost setup` to consent)

## [0.1.1] — Unreleased

### Added
- `--show-as` parameter on `cal add` / `cal update` CLI commands and MCP tools (`free`, `tentative`, `busy`, `oof`, `workingElsewhere`) (#2)
- `teams_workspace_extract` MCP tool — extracts plain text from DOCX, XLSX, PPTX, and PDF files in the workspace (no filesystem server needed)
- Binary file handling in `teams_workspace_read` — returns path hint instead of crashing on non-UTF-8 files
- Filesystem Server setup docs in README for reading binary files (DOCX, PDF, XLSX) in Claude Desktop
- Known Limitations section in README

### Fixed
- `cal_add` / `cal_update`: bare ISO timestamps now include `timeZone` property from config, preventing UTC default shift (#3)
- Added `timezone` config setting (set during `outpost setup`, defaults to `UTC`)
- `--timezone` / `--tz` CLI flag and `timezone` MCP parameter for per-event override

## [0.1.0] — 2026-02-28

Initial release.

- CLI for Tasks, Calendar, Email, Contacts, Teams via Microsoft Graph API
- 35-tool MCP server for Claude Desktop integration
- MSAL device code auth with encrypted token cache
- Natural-language date parsing
- Rich table and JSON output modes
- Retry/backoff on HTTP 429, pagination support
- Multi-account profiles (`--profile`)
- Teams file workspace (download, read, write, upload)
- 280 tests
