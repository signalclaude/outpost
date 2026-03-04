# outpost

Your outpost to Outlook — from the terminal.

A fast CLI for Microsoft **Tasks**, **Calendar**, **Email**, **Contacts**, and **Teams** via the Microsoft Graph API. Human-friendly with natural-language dates, AI-agent-ready with JSON output and an MCP server for Claude Desktop.

## How Does It Compare?

| Feature | **outpost** | Outlook Desktop | OWA (Browser) | python-o365 | msgraph-sdk |
|---|:---:|:---:|:---:|:---:|:---:|
| Terminal-native | **Yes** | No | No | Library only | Library only |
| Natural language dates | **Yes** | No | No | No | No |
| Tasks + Calendar + Mail + Teams | **All-in-one** | Yes | Yes | Partial | Raw API |
| MCP server (Claude Desktop) | **35 tools** | No | No | No | No |
| JSON output for scripting | **Every command** | No | No | Manual | Manual |
| Multi-account profiles | **Yes** | Yes | Tab switching | Manual | Manual |
| Optional permission scopes | **Opt-in per feature** | All or nothing | All or nothing | Manual | Manual |
| Runs headless / SSH | **Yes** | No | No | Yes | Yes |
| Setup time | **< 2 minutes** | Installer | Browser login | Code required | Code required |

## Why?

- **No more context switching** — manage Outlook without leaving the terminal
- **Natural language dates** — `tomorrow 9am`, `next friday`, `in 2 hours`
- **AI-agent ready** — JSON output mode on every command, plus a built-in MCP server with 35 tools
- **One tool** for Tasks, Calendar, Email, Contacts, and Teams
- **Optional features** — Teams requires extra permissions, so it's opt-in during setup

## Quick Start

```bash
# Install
pip install -e .

# Connect your Microsoft account
outpost setup

# You're ready
outpost task list
outpost cal today
outpost mail list --unread
```

## Setup

### Prerequisites
- Python 3.10+
- A Microsoft 365 account (personal or work/school)

### Install from source
```bash
git clone https://github.com/YOUR_USERNAME/outpost.git
cd outpost
pip install -e ".[dev]"
```

### First Run
```bash
outpost setup
```

This walks you through connecting your Microsoft account using device code flow. You'll be prompted to optionally enable Teams access (requires additional permissions — see [Permissions](docs/permissions.md)).

### Multi-Account Support
```bash
outpost --profile work setup
outpost --profile personal setup
outpost --profile work cal today
```

## Commands

### Tasks (Microsoft To Do)
```bash
outpost task add "Review PR" --due tomorrow --priority high
outpost task list                         # all tasks
outpost task list --due today             # tasks due today
outpost task list --list "Work"           # tasks in a specific list
outpost task update <id> --title "New title"
outpost task complete <id>
outpost task delete <id>
outpost task lists                        # list all task lists
outpost task lists-create "Shopping"
outpost task lists-delete <list-id>
```

### Calendar
```bash
outpost cal add "Standup" --start "tomorrow 9am" --duration 15
outpost cal add "Review" --start "friday 2pm" --end "friday 3pm" --attendee alice@work.com
outpost cal today                         # today's events
outpost cal next                          # next upcoming event
outpost cal next --count 5                # next 5 events
outpost cal list --week                   # this week
outpost cal list --date "next monday"     # specific day
outpost cal update <id> --title "New title"
outpost cal delete <id>
```

### Email
```bash
outpost mail list                         # recent inbox
outpost mail list --unread                # unread only
outpost mail list --folder sentitems      # sent items
outpost mail read <id>                    # read a message
outpost mail read <id> --download         # read + download attachments
outpost mail send --to "bob@work.com" --subject "Update" --body "All good!"
outpost mail send --to "bob@work.com" --subject "Report" --body "See attached" --attach report.pdf
outpost mail reply <id> --body "Thanks!"
outpost mail search "quarterly report"
outpost mail delete <id>
```

### Contacts
```bash
outpost contact list                      # all contacts
outpost contact search "alice"            # search by name or email
```

### Teams (opt-in)
Requires enabling Teams during `outpost setup`. See [Permissions](docs/permissions.md) for details.

```bash
outpost teams list                        # your joined teams
outpost teams channels <team-id>          # channels in a team
outpost teams messages <team-id> <channel-id>          # read messages
outpost teams send <team-id> <channel-id> --body "Hi team!"
outpost teams files <team-id> <channel-id>             # SharePoint files
outpost teams download <drive-id> <item-id>            # download a file
outpost teams upload <drive-id> <parent-id> report.pdf # upload a file
```

### Global Options
- `--output json|table` — output format (default: table). JSON mode on every command for scripting and AI agents
- `--profile <name>` — use a named profile for multi-account support
- `--full-id` — show full IDs on list commands (default: truncated to 8 chars)

## MCP Server (Claude Desktop Integration)

Outpost includes a built-in MCP server with 35 tools, enabling Claude Desktop to manage your Outlook directly.

### Setup for Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "outpost": {
      "command": "outpost-mcp",
      "args": []
    }
  }
}
```

Or run manually:
```bash
outpost mcp serve                         # stdio (default)
outpost mcp serve --transport sse --port 8080  # SSE transport
```

### MCP Tools

| Category | Tools |
|----------|-------|
| Tasks | `task_add`, `task_list`, `task_update`, `task_complete`, `task_delete`, `task_lists`, `task_lists_create`, `task_lists_delete` |
| Calendar | `cal_add`, `cal_today`, `cal_list`, `cal_next`, `cal_update`, `cal_delete` |
| Email | `mail_list`, `mail_read`, `mail_send`, `mail_reply`, `mail_delete`, `mail_search`, `mail_attachments`, `mail_download_attachment` |
| Contacts | `contact_list`, `contact_search` |
| Teams | `teams_list`, `teams_channels`, `teams_messages`, `teams_send`, `teams_files`, `teams_download`, `teams_upload` |
| Workspace | `teams_workspace_list`, `teams_workspace_read`, `teams_workspace_write`, `teams_workspace_extract` |
| Auth | `auth_status` |

### MCP Workspace

Teams file operations use a transient workspace directory (`%TEMP%/outpost/workspace`) so Claude Desktop can download, read, and share files:

1. `teams_download` — download a file from Teams to the workspace
2. `teams_workspace_extract` — extract text from binary files (DOCX, XLSX, PPTX, PDF)
3. `teams_workspace_read` — read text files (markdown, CSV, plain text)
4. `teams_workspace_write` — create text files for sharing (markdown, CSV, etc.)
5. `teams_upload` — upload text files to Teams/SharePoint

Binary files (DOCX, XLSX, PPTX, PDF) are read-only — extract and analyze their content, but don't modify and re-upload them (formatting would be lost).

The workspace is automatically cleaned each time the MCP server starts.

#### Reading Binary Files (DOCX, PDF, XLSX, etc.)

`teams_workspace_read` handles plain text files. For binary files, add the official [MCP Filesystem Server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) alongside Outpost so Claude Desktop can read files directly from the workspace:

```json
{
  "mcpServers": {
    "outpost": {
      "command": "outpost-mcp",
      "args": []
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "<workspace-path>"
      ]
    }
  }
}
```

Replace `<workspace-path>` with the actual workspace directory on your system. To find it, run:
```bash
python -c "import tempfile; print(tempfile.gettempdir() + '/outpost/workspace')"
```

Use double backslashes in the JSON config on Windows (e.g. `C:\\Temp\\outpost\\workspace`). When Claude downloads a binary file via `teams_download`, it will automatically use the filesystem server to read it at the returned workspace path.

## Authentication

Outpost uses MSAL device code flow with a pre-registered multi-tenant Azure AD app. Token caching uses OS-level encryption where available (DPAPI on Windows, Keychain on macOS, libsecret on Linux).

For details on which permissions are required and how optional features work, see [Permissions](docs/permissions.md).

## Known Limitations

- **Binary file performance via MCP Filesystem Server** — Reading and writing binary files (DOCX, PDF, XLSX) through the MCP Filesystem Server is slow. The server must parse the file through a Python subprocess, which adds significant latency for larger documents. Plain text files via `teams_workspace_read` are fast.
- **Upload size limit** — `teams_upload` uses simple PUT upload, limited to files under 4 MB. Larger files require the Graph API upload session workflow, which is not yet implemented.
- **Contacts are read-only** — `contact_list` and `contact_search` support reading only. Write/update/delete operations are not yet available.
- **No multi-user OAuth** — Each profile uses a single device code flow. Delegated multi-user auth (e.g. shared app with per-user tokens) is not yet supported.
- **Calendar timezone** — Requires manual configuration via `outpost setup`. There is no auto-detection of the user's local timezone.

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests (293 passing)
pytest

# Run tests with verbose output
pytest -v
```

### Project Structure
```
src/outpost/
  api/           # Graph API modules (tasks, calendar, mail, contacts, teams)
  formatters/    # Rich table + JSON output formatters
  utils/         # Date parsing utilities
  cli.py         # Typer CLI commands
  config.py      # Configuration, scopes, workspace
  auth.py        # MSAL device code flow
  mcp_server.py  # FastMCP server (35 tools)
tests/           # pytest + respx mocked tests
```

## License

MIT
