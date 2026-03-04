# Claude Code Kickoff Prompt

Paste this into Claude Code to get started. Run from `C:\repos\outpost`.

---

I want to build an open-source Python CLI tool called **outpost** — a fast, natural-language-friendly command-line interface to Microsoft Outlook via the Microsoft Graph API. Think of it as a unified CLI for Outlook **Tasks/To Do**, **Calendar**, and **Email** — designed to be both human-friendly and AI-agent-friendly.

The name "outpost" is a play on Outlook — it's your outpost to the Outlook world from the terminal.

## Core Requirements

### Authentication
- Use Microsoft Graph API with MSAL (device code flow for initial auth, refresh tokens after that)
- Store tokens securely (OS keychain via `keyring` library, fallback to encrypted file)
- Support multiple accounts (personal + work)
- Guide the user through Azure AD app registration on first run

### Commands — Tasks (Microsoft To Do)
```
outpost task add "Review PR for auth module" --due tomorrow --time 9am --list "Work"
outpost task add "Buy groceries" --due today --priority high
outpost task list                          # show all tasks
outpost task list --due today              # tasks due today
outpost task list --list "Work"            # tasks in a specific list
outpost task complete <task-id>
outpost task delete <task-id>
```

### Commands — Calendar
```
outpost cal add "Team standup" --start "tomorrow 9:00" --end "tomorrow 9:30"
outpost cal add "Lunch with Sarah" --start "2026-03-05 12:00" --duration 60
outpost cal list                           # upcoming events
outpost cal list --date tomorrow
outpost cal list --week
outpost cal today                          # shortcut for today's schedule
outpost cal delete <event-id>
```

### Commands — Email
```
outpost mail list                          # recent inbox
outpost mail list --unread
outpost mail read <message-id>
outpost mail send --to "bob@work.com" --subject "Quick update" --body "Here's the status..."
outpost mail search "quarterly report"
```

### Commands — Setup
```
outpost setup                              # interactive first-time setup wizard
outpost auth add <account-name>            # add an account
outpost auth status                        # show auth status
outpost config                             # show/edit config
```

## Technical Stack
- **Python 3.10+**
- **Click** for CLI framework
- **MSAL** (`msal` package) for authentication
- **httpx** or **requests** for Graph API calls (or use `python-o365` as a higher-level wrapper — evaluate tradeoffs)
- **keyring** for secure token storage
- **python-dateutil** / **parsedatetime** for natural language date parsing
- **rich** for pretty terminal output (tables, colors, spinners)
- **JSON output mode** (`--json` flag on all commands) for AI agent integration

## Project Structure
```
outpost/
├── README.md
├── pyproject.toml
├── LICENSE                  # MIT
├── src/
│   └── outpost/
│       ├── __init__.py
│       ├── cli.py           # Click CLI entry point
│       ├── auth.py          # MSAL auth + token management
│       ├── config.py        # Config file management
│       ├── api/
│       │   ├── __init__.py
│       │   ├── tasks.py     # Microsoft To Do operations
│       │   ├── calendar.py  # Calendar operations
│       │   └── mail.py      # Mail operations
│       ├── formatters/
│       │   ├── __init__.py
│       │   ├── table.py     # Rich table output
│       │   └── json.py      # JSON output for agents
│       └── utils/
│           ├── __init__.py
│           └── dates.py     # Natural language date parsing
├── tests/
│   ├── test_tasks.py
│   ├── test_calendar.py
│   └── test_mail.py
└── docs/
    ├── setup-guide.md       # Azure AD app registration walkthrough
    └── agent-integration.md # How to use with Claude, etc.
```

## Key Design Decisions
1. **Natural language dates first** — `tomorrow 9am`, `next friday`, `in 2 hours` should all just work
2. **Sensible defaults** — `outpost task add "thing"` with no flags = due today, normal priority
3. **JSON mode everywhere** — every command supports `--json` for piping and AI agent use
4. **Minimal config** — first run wizard handles everything, sane defaults after that
5. **Error messages that help** — if auth fails, tell them exactly what to fix

## Phase 1 (MVP)
Start with:
1. Auth setup (device code flow + token caching)
2. `outpost task add` and `outpost task list`
3. `outpost cal add` and `outpost cal today`
4. Pretty output with `rich`

## Phase 2
- Full CRUD for tasks, calendar, email
- `--json` flag on everything
- Multiple account support
- `outpost mail send`

## Phase 3
- Natural language mode: `outpost "schedule a meeting with Bob tomorrow at 2pm"`
- Shell completions (bash/zsh/fish/PowerShell)
- Recurring events and tasks
- Config profiles

Please start by setting up the project structure, pyproject.toml with dependencies, and implement Phase 1. Walk me through the Azure AD app registration steps I'll need to do in my browser before we can test.
