# Permissions & Scopes

Outpost uses Microsoft Graph API OAuth 2.0 scopes to access your data. Scopes are split into **core** (always required) and **optional** (opt-in per feature during `outpost setup`).

## Core Scopes (Always Required)

These scopes are requested whenever you run `outpost setup`. They cover Tasks, Calendar, Email, and Contacts.

| Scope | Consent Type | Used By |
|-------|-------------|---------|
| `User.Read` | User | Auth status, profile info |
| `Tasks.ReadWrite` | User | All `task` commands — add, list, update, complete, delete, list management |
| `Calendars.ReadWrite` | User | All `cal` commands — add, list, today, next, update, delete |
| `Mail.ReadWrite` | User | `mail list`, `mail read`, `mail search`, `mail delete`, attachments |
| `Mail.Send` | User | `mail send`, `mail reply` |
| `Contacts.Read` | User | `contact list`, `contact search` |

**All core scopes use user (delegated) consent** — no admin approval needed. Any Microsoft 365 user can consent to these.

## Optional: Teams Scopes

Teams scopes are **only requested if you enable Teams** during `outpost setup`. Some of these may require admin consent depending on your organization's policies.

| Scope | Consent Type | Used By |
|-------|-------------|---------|
| `Team.ReadBasic.All` | User or Admin* | `teams list` — list your joined teams |
| `Channel.ReadBasic.All` | User or Admin* | `teams channels` — list channels in a team |
| `ChannelMessage.Read.All` | Admin | `teams messages` — read channel messages |
| `ChannelMessage.Send` | User | `teams send` — send channel messages |
| `Chat.Read` | User | `teams chats`, `teams chat-messages` — list chats and read chat messages |
| `ChatMessage.Send` | User | `teams chat-send` — send messages to chats |
| `Files.Read.All` | User or Admin* | `teams files`, `teams download` — browse and download SharePoint files |

\* *Some organizations restrict these scopes to admin consent only. If you encounter a "needs admin approval" error, ask your IT administrator to consent on your behalf, or disable Teams in outpost.*

## How Optional Scopes Work

During `outpost setup`, you'll be prompted:

```
Optional features (require additional permissions):
  Microsoft Teams — read/send channel messages, browse channel files

Enable Teams access? (your admin may need to approve) [y/N]:
```

- **If you say yes**: Teams scopes are added to the consent request. You'll see them listed in the Microsoft login consent screen.
- **If you say no**: Only core scopes are requested. Teams commands will show a helpful error directing you back to `outpost setup`.

Your choice is saved in the config file (`enabled_features` array). You can re-run `outpost setup` at any time to change it.

## Scope-to-Feature Matrix

### Tasks

| Command | Scope Required |
|---------|---------------|
| `task add` | `Tasks.ReadWrite` |
| `task list` | `Tasks.ReadWrite` |
| `task update` | `Tasks.ReadWrite` |
| `task complete` | `Tasks.ReadWrite` |
| `task delete` | `Tasks.ReadWrite` |
| `task lists` | `Tasks.ReadWrite` |
| `task lists-create` | `Tasks.ReadWrite` |
| `task lists-delete` | `Tasks.ReadWrite` |

### Calendar

| Command | Scope Required |
|---------|---------------|
| `cal add` | `Calendars.ReadWrite` |
| `cal today` | `Calendars.ReadWrite` |
| `cal list` | `Calendars.ReadWrite` |
| `cal next` | `Calendars.ReadWrite` |
| `cal update` | `Calendars.ReadWrite` |
| `cal delete` | `Calendars.ReadWrite` |

### Email

| Command | Scope Required |
|---------|---------------|
| `mail list` | `Mail.ReadWrite` |
| `mail read` | `Mail.ReadWrite` |
| `mail send` | `Mail.ReadWrite`, `Mail.Send` |
| `mail reply` | `Mail.ReadWrite`, `Mail.Send` |
| `mail delete` | `Mail.ReadWrite` |
| `mail search` | `Mail.ReadWrite` |

### Contacts

| Command | Scope Required |
|---------|---------------|
| `contact list` | `Contacts.Read` |
| `contact search` | `Contacts.Read` |

### Teams (Optional)

| Command | Scope Required |
|---------|---------------|
| `teams list` | `Team.ReadBasic.All` |
| `teams channels` | `Channel.ReadBasic.All` |
| `teams messages` | `ChannelMessage.Read.All` |
| `teams send` | `ChannelMessage.Send` |
| `teams files` | `Files.Read.All`, `Channel.ReadBasic.All` |
| `teams download` | `Files.Read.All` |
| `teams chats` | `Chat.Read` |
| `teams chat-messages` | `Chat.Read` |
| `teams chat-send` | `ChatMessage.Send` |
| `teams upload` | `Files.Read.All`* |

\* *Upload currently uses `Files.Read.All` which permits reading. For write operations, your organization's SharePoint permissions determine actual access. A future version may add `Files.ReadWrite.All` for explicit write consent.*

## MCP Tools

MCP tools use the same scopes as their CLI counterparts. Teams MCP tools (`teams_list`, `teams_channels`, `teams_chats`, etc.) are feature-gated — they return a clear error message if Teams is not enabled in the config.

The MCP workspace tools (`teams_workspace_list`, `teams_workspace_read`, `teams_workspace_write`) operate on the local transient workspace directory and do not require any Graph API scopes.

## Troubleshooting

### "Need admin approval"
Your organization requires admin consent for one or more scopes. Options:
1. Ask your IT admin to grant consent for your user or the entire organization
2. Re-run `outpost setup` and decline the Teams feature to use only core scopes

### "Insufficient privileges"
The token was acquired without the needed scope. Re-run `outpost setup` to re-consent with the correct scopes.

### "Token expired"
Run `outpost setup` to re-authenticate. Outpost uses refresh tokens, so this should be rare.

### Teams commands show "feature not enabled"
Run `outpost setup` and answer "y" to the Teams prompt. This adds Teams scopes to your consent and saves the preference.
