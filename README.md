# XGC Discord Bot Remote Operations
[![Discord Widget](https://discord.com/api/guilds/829181609156411463/widget.png?style=banner2)](https://discord.gg/Xieon)


> Created by **Xieons-Gaming-Corner**  
> Lead Developer: **Xieon**

[![XGC Discord](https://img.shields.io/badge/XGC%20Support-Discord-5865F2?logo=discord&logoColor=white)](https://discord.gg/xieon)
[![GitHub Organization](https://img.shields.io/badge/GitHub-Xieons--Gaming--Corner-181717?logo=github)](https://github.com/Xieons-Gaming-Corner)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)

A local Python utility for managing Discord application commands and basic bot-guild operations through Discord’s API.

- **Official XGC Community and Support Server:** [discord.gg/xieon](https://discord.gg/xieon)
- **Official XGC GitHub Organization:** [Xieons-Gaming-Corner](https://github.com/Xieons-Gaming-Corner)
- **Repository:** [Discord Slash Command Wiper](https://github.com/Xieons-Gaming-Corner/Discord_Slash_Command_Wiper)

---

## Overview

XGC Discord Bot Remote Operations is a command-line utility that authenticates with a Discord **bot token** and provides local management actions for the associated Discord application.

The program includes command cleanup, global-command replacement, bot-guild inventory, optional guild removal, application installation statistics, rate-limit handling, and a local audit log.

> This tool is intended for bot owners and authorized application administrators. Never share bot tokens or request Discord user tokens.

---

## Features

The tool provides the following menu:

```text
Discord Bot Remote Operations

What bot remote operation do you want to do?

  1. Remove server-specific slash commands
  2. Remove global slash commands
  3. Create /placeholder and overwrite global commands
  4. View guilds / remove the bot from a selected guild
  5. View application install / authorization statistics
  6. Exit
```

| Option | Operation | Description |
|---:|---|---|
| 1 | Remove server-specific slash commands | Lists and optionally removes type-1 chat-input commands for one selected guild/server |
| 2 | Remove global slash commands | Lists and optionally removes global type-1 chat-input commands |
| 3 | Create `/placeholder` | Replaces every global application command with one placeholder slash command |
| 4 | View or leave guilds | Lists guilds where the bot is present and allows leaving one selected guild |
| 5 | View application statistics | Shows approximate Discord install and OAuth authorization counts when returned by Discord |
| 6 | Exit | Closes the tool safely |

---

## Requirements

- Python **3.9 or newer**
- A Discord bot token for an application you own or are authorized to manage
- Internet access
- The Python `requests` package

Install the required package:

```bash
pip install requests
```

---

## Running the Tool

Run the Python script from a terminal or command prompt:

```bash
python discord_bot_remote_operations.py
```

The program prompts for a bot token:

```text
Discord BOT token (hidden):
```

The token input is hidden while typing.

You may enter the token either with or without the Discord `Bot ` prefix:

```text
Bot YOUR_BOT_TOKEN
```

or:

```text
YOUR_BOT_TOKEN
```

The program removes the `Bot ` prefix automatically when present.

After successful authentication, the tool displays the application name and application ID:

```text
Authenticated application: Example Bot (123456789012345678)
```

---

## Option 1: Server Slash Commands

This option lists slash commands registered specifically in one Discord server.

The tool requests a numeric server ID:

```text
Server ID:
```

It then lists all detected chat-input slash commands:

```text
Application: Example Bot (123456789012345678)
Target server: 987654321098765432
Server slash commands found: 2

  /ping
  /setup
```

To delete the listed server commands, enter the exact confirmation text:

```text
DELETE SERVER
```

Any other input cancels the operation.

### Scope

This option removes only:

- Guild/server-specific commands
- Chat-input slash commands
- Discord application command type `1`

It does not remove:

- Global commands
- User context-menu commands
- Message context-menu commands
- Commands from another Discord application

---

## Option 2: Global Slash Commands

This option lists global slash commands registered for the bot application.

Example:

```text
Application: Example Bot (123456789012345678)
Global slash commands found: 3

  /ping
  /raid
  /settings
```

To delete all listed global slash commands, enter:

```text
DELETE GLOBAL
```

Any other input cancels the operation.

### Important Warning

Global slash commands may be available across every server and user installation where the application is available.

This option removes only global type-1 chat-input commands. It does not remove global context-menu commands.

Global command updates can take time to propagate through Discord clients. If old commands remain visible:

1. Restart or refresh Discord.
2. Wait for Discord propagation.
3. Check whether your bot’s own command-registration code is automatically recreating commands.

---

## Option 3: Create `/placeholder`

This option uses Discord’s global application-command bulk-overwrite endpoint.

It replaces **every global application command** with exactly one global slash command:

```text
/placeholder
```

The command uses this description:

```text
This command is a placeholder and will fail
```

The tool displays existing global commands before making any change:

```text
Existing global application commands: 2

  ping (type 1)
  View Profile (type 2)
```

Then it warns that the operation replaces all global commands, including:

- Global slash commands
- User context-menu commands
- Message context-menu commands

To continue, enter the exact confirmation:

```text
OVERWRITE GLOBAL
```

### Expected Placeholder Behavior

The tool registers `/placeholder`, but it does not run a persistent Discord interaction handler.

If no separately running bot process or interaction webhook responds to the command, Discord will show an interaction failure when a user invokes it.

That behavior is intentional for this placeholder command.

### Result

After a successful overwrite, the global application-command list contains only:

```text
/placeholder
```

with this description:

```text
This command is a placeholder and will fail
```

---

## Option 4: View Guilds / Leave a Guild

This option retrieves the guilds where the authenticated bot is currently present.

Example output:

```text
Example Bot is currently in 3 guild(s):

  1. XGC Community (ID: 111111111111111111)
  2. Test Server (ID: 222222222222222222)
  3. Development Server (ID: 333333333333333333)
```

To remove the bot from a listed server, enter its displayed number:

```text
Enter a guild number to remove the bot from it:
```

The tool then displays the selected guild details and requires this exact confirmation:

```text
LEAVE GUILD
```

Example:

```text
WARNING: This will remove Example Bot from:

  Server: Test Server
  Guild ID: 222222222222222222

Type LEAVE GUILD to remove the bot from this server:
```

### Scope

This operation:

- Removes the bot from only the selected guild
- Does not delete the server
- Does not remove server members
- Does not delete messages, channels, roles, or data
- Does not remove the application’s global commands
- Does not revoke OAuth authorization from individual users

---

## Option 5: Application Statistics

This option displays aggregate counts returned by Discord’s application API.

Example:

```text
Application Installation / Authorization Statistics
--------------------------------------------------------
Application: Example Bot (123456789012345678)

Approximate server installs: 4
Approximate individual-user installs: 1
Approximate individual-user OAuth authorizations: 1
```

The available values may include:

| Value | Meaning |
|---|---|
| Approximate server installs | Approximate number of guild/server installations |
| Approximate individual-user installs | Approximate number of user installs |
| Approximate individual-user OAuth authorizations | Approximate number of users with OAuth2 authorization for the application |

### Limitations

Discord returns aggregate totals only.

This tool cannot use a bot token to:

- List every individual user who installed the application
- Identify the specific person represented by a user-install count
- List every OAuth-authorized user
- Globally revoke OAuth authorization for all users
- Collect or use Discord user tokens

OAuth revocation requires an OAuth token your own application previously received through a properly authorized OAuth flow and securely stored.

---

## Logging

The program writes a local audit log named:

```text
slash_cleaner_logs.txt
```

The file is created automatically if it does not exist.

### Log Location

| How the tool is launched | Log location |
|---|---|
| Python script | Same directory as the `.py` file |
| Compiled executable | Same directory as the `.exe` file |

Example:

```text
Discord_Slash_Command_Wiper/
├── discord_bot_remote_operations.py
└── slash_cleaner_logs.txt
```

### Logged Events

The log may include:

- Tool startup and closure
- Application name and application ID
- Guild IDs selected by the user
- Names of discovered slash commands
- Deletion confirmations and cancellations
- Deleted command IDs
- Global command overwrite events
- Guild inventory results
- Guild-leave actions
- Application statistics lookups
- Discord API errors
- Rate-limit retry events
- Keyboard interruption events

### Secrets Are Not Logged

The tool is designed not to write the following to the log:

- Discord bot tokens
- OAuth access tokens
- OAuth refresh tokens
- Passwords
- Other user-provided secrets

Example log entries:

```text
[2026-10-13 17:37:14] Discord Bot Remote Operations started.
[2026-10-13 17:37:17] Authenticated application; name=Example Bot; application_id=123456789012345678.
[2026-10-13 17:37:26] Found 2 global slash command(s); commands=/ping, /setup.
[2026-10-13 17:37:32] Global slash-command deletion cancelled.
[2026-10-13 17:37:41] HTTP session closed.
```

---

## Confirmation Protections

Destructive or high-impact operations require an exact typed confirmation.

| Action | Required confirmation |
|---|---|
| Delete server-specific slash commands | `DELETE SERVER` |
| Delete global slash commands | `DELETE GLOBAL` |
| Replace all global application commands with `/placeholder` | `OVERWRITE GLOBAL` |
| Remove the bot from a selected server | `LEAVE GUILD` |

If the entered text does not match exactly, the requested operation is cancelled.

---

## Rate Limits and Errors

The program automatically handles Discord API rate-limit responses.

When Discord returns HTTP `429`, the tool:

1. Reads Discord’s `retry_after` value.
2. Waits for the required duration plus a small buffer.
3. Retries the request.
4. Stops after five failed rate-limit retries.

API errors are printed in the console and written to `slash_cleaner_logs.txt`.

Example:

```text
Error: Discord returned HTTP 403: Missing Access
```

Common causes include:

- Invalid or expired bot token
- Incorrect server ID
- The bot is not installed in the selected guild
- Insufficient authorization for the requested action
- A command was removed or changed before deletion completed
- Discord API availability or rate-limit restrictions

---

## Command Re-registration Warning

Deleting commands through this tool does not prevent your actual bot application from registering them again.

Your bot may recreate commands automatically if its source code deploys or syncs commands on startup.

Examples include:

```python
await bot.tree.sync()
```

or command-registration/deployment scripts used by Discord.py, Discord.js, Eris, nextcord, pycord, or other Discord libraries.

Before using this tool to permanently remove commands:

1. Find the command-registration code in the bot project.
2. Remove or disable unwanted command definitions.
3. Stop automatic command synchronization if necessary.
4. Restart the bot only after correcting the registration code.

Otherwise, commands may return after the bot restarts.

---

## Security Guidance

- Keep your bot token private.
- Do not put tokens in GitHub repositories.
- Do not share tokens in screenshots, Discord messages, support tickets, or public chat logs.
- Rotate the bot token in the Discord Developer Portal immediately if it is exposed.
- Never request or collect user Discord account tokens.
- Use this tool only with applications you own or are explicitly authorized to administer.
- Review command lists carefully before entering destructive confirmations.

---

## Disclaimer

This project is an independent Xieons-Gaming-Corner utility. It is not affiliated with, endorsed by, sponsored by, or officially associated with Discord.

Use this tool responsibly and in compliance with:

- Discord Terms of Service
- Discord Developer Terms
- Discord API documentation
- Applicable laws and community rules

---

## Credits

Created by **Xieons-Gaming-Corner**  
Lead Developer: **Xieon**

- [XGC Official Community and Support Server](https://discord.gg/xieon)
- [Xieons-Gaming-Corner GitHub Organization](https://github.com/Xieons-Gaming-Corner)
- [Discord Slash Command Wiper Repository](https://github.com/Xieons-Gaming-Corner/Discord_Slash_Command_Wiper)

Feel free to use this tool if it helps you. If you use any part of it in another project, please credit **Xieons-Gaming-Corner (XGC)**.
