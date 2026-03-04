# ⛺ outpost

Your outpost to Outlook — from the terminal.

A fast, natural-language-friendly CLI for Microsoft Outlook **Tasks**, **Calendar**, and **Email** via the Microsoft Graph API. Designed to be both human-friendly and AI-agent-friendly.

## Why?

- **No more clicking through Outlook's UI** for quick tasks
- **Natural language dates** — `tomorrow 9am`, `next friday`, `in 2 hours`
- **AI-agent ready** — JSON output mode on every command, perfect for use with Claude, GPT, etc.
- **One tool** for Tasks, Calendar, and Email

## Quick Examples

```bash
# Add a task due tomorrow at 9am
outpost task add "Review PR for auth module" --due tomorrow --time 9am

# See today's calendar
outpost cal today

# Add a meeting
outpost cal add "Team standup" --start "tomorrow 9:00" --duration 30

# Check unread emails
outpost mail list --unread

# Send a quick email
outpost mail send --to "bob@work.com" --subject "Status update" --body "All good!"

# JSON output for scripting / AI agents
outpost task list --json
```

## Setup

### Prerequisites
- Python 3.10+
- A Microsoft 365 account (personal or work/school)
- An Azure AD app registration ([setup guide](docs/setup-guide.md))

### Install
```bash
pip install outpost-cli
```

Or from source:
```bash
git clone https://github.com/YOUR_USERNAME/outpost.git
cd outpost
pip install -e .
```

### First Run
```bash
outpost setup
```

This walks you through connecting your Microsoft account. You'll need your Azure AD client ID — see the [setup guide](docs/setup-guide.md) for a 5-minute walkthrough.

## Commands

### Tasks (Microsoft To Do)
| Command | Description |
|---------|-------------|
| `outpost task add "title"` | Add a task |
| `outpost task list` | List tasks |
| `outpost task list --due today` | Tasks due today |
| `outpost task complete <id>` | Mark complete |
| `outpost task delete <id>` | Delete a task |

### Calendar
| Command | Description |
|---------|-------------|
| `outpost cal add "title" --start "..."` | Create event |
| `outpost cal today` | Today's schedule |
| `outpost cal list --week` | This week's events |
| `outpost cal delete <id>` | Delete an event |

### Email
| Command | Description |
|---------|-------------|
| `outpost mail list` | Recent inbox |
| `outpost mail list --unread` | Unread only |
| `outpost mail read <id>` | Read a message |
| `outpost mail send --to "..." --subject "..."` | Send email |
| `outpost mail search "query"` | Search messages |

### Global Options
- `--json` — JSON output on any command (for scripting and AI agents)
- `--account <name>` — Use a specific account (multi-account support)

## AI Agent Integration

Every command supports `--json` output, making it easy to integrate with AI tools:

```bash
# Pipe your schedule to an AI for analysis
outpost cal today --json | claude "What's my next meeting?"

# Automate task creation from any AI workflow
outpost task add "$(claude 'what should I work on next?')" --due today
```

See [agent-integration.md](docs/agent-integration.md) for more details.

## Roadmap

- [x] Auth via device code flow
- [x] Tasks — add, list, complete
- [x] Calendar — add, list, today view
- [ ] Email — list, read, send, search
- [ ] Multi-account support
- [ ] Natural language mode (`outpost "schedule lunch with Sarah Friday"`)
- [ ] Shell completions (bash/zsh/fish/PowerShell)
- [ ] Recurring events and tasks

## Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT
