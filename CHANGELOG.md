# Changelog

All notable changes to Outpost are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/).

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
