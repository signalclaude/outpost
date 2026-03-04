# outpost

Your outpost to Outlook — from the terminal.

A fast CLI for Microsoft **Tasks**, **Calendar**, **Email**, **Contacts**, and **Teams** via the Microsoft Graph API. Human-friendly with natural-language dates, AI-agent-ready with JSON output and a 39-tool MCP server for Claude Desktop.

**[Full documentation on the Wiki](https://github.com/signalclaude/outpost/wiki)**

## How Does It Compare?

| Feature | **outpost** | Outlook Desktop | OWA (Browser) | python-o365 | msgraph-sdk |
|---|:---:|:---:|:---:|:---:|:---:|
| Terminal-native | **Yes** | No | No | Library only | Library only |
| Natural language dates | **Yes** | No | No | No | No |
| Tasks + Calendar + Mail + Teams | **All-in-one** | Yes | Yes | Partial | Raw API |
| Teams channel files (browse/download) | **Yes** | Yes | Yes | No | Raw API |
| Office/PDF text extraction (DOCX, XLSX, PPTX, PDF) | **Built-in** | Native | Native | No | No |
| MCP server (Claude Desktop) | **39 tools** | No | No | No | No |
| JSON output for scripting | **Every command** | No | No | Manual | Manual |
| Multi-account profiles | **Yes** | Yes | Tab switching | Manual | Manual |
| Optional permission scopes | **Opt-in per feature** | All or nothing | All or nothing | Manual | Manual |
| Runs headless / SSH | **Yes** | No | No | Yes | Yes |
| Setup time | **< 2 minutes** | Installer | Browser login | Code required | Code required |

## Quick Start

```bash
# Install (Python 3.10+)
pip install git+https://github.com/signalclaude/outpost.git

# Connect your Microsoft account
outpost setup

# You're ready
outpost task list
outpost cal today
outpost mail list --unread
outpost teams chats
```

## What Can It Do?

```bash
outpost task add "Review PR" --due tomorrow --priority high
outpost cal add "Standup" --start "tomorrow 9am" --duration 15
outpost mail send --to "bob@work.com" --subject "Update" --body "All good!"
outpost teams send <team-id> <channel-id> --body "Hi team!"
outpost contact search "alice"
outpost update                            # self-update to latest release
outpost --version                         # check installed version
```

Every command supports `--output json` for scripting and AI agents.

## Documentation

See the **[Wiki](https://github.com/signalclaude/outpost/wiki)** for full documentation:

- [Installation](https://github.com/signalclaude/outpost/wiki/Installation) — pip, wheel, from source
- [Setup & Authentication](https://github.com/signalclaude/outpost/wiki/Setup-&-Authentication) — device code flow, token storage
- [Commands](https://github.com/signalclaude/outpost/wiki/Commands--Tasks) — Tasks, Calendar, Email, Contacts, Teams
- [MCP Server](https://github.com/signalclaude/outpost/wiki/MCP-Server--Local-Setup) — Claude Desktop integration (39 tools)
- [Remote Access](https://github.com/signalclaude/outpost/wiki/MCP-Server--Remote-Access) — SSE/streamable-http for mobile/LAN
- [Permissions & Scopes](https://github.com/signalclaude/outpost/wiki/Permissions-&-Scopes) — scope-to-feature matrix

## License

MIT
