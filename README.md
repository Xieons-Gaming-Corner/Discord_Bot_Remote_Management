# Discord_Slash_Command_Wiper  
A simple, but useful took. 
Takes Discord token and server ID and wipes slash commands from server
<img width="960" height="322" alt="image" src="https://github.com/user-attachments/assets/877b5a40-e773-460a-a4c7-f72317f8c093" />


# Discord Slash Command Clearer

A standalone Windows utility for removing a bot’s server-specific slash commands from a selected Discord server.

The tool is useful for clearing old command registrations during bot development, removing outdated commands, or preparing for a fresh command registration.

## What it does

The Slash Command Clearer:

- Prompts for a Discord bot token using hidden input.
- Prompts for the target server ID.
- Identifies the application associated with the token.
- Lists that bot’s server-specific slash commands.
- Requires you to type **DELETE** before removing anything.
- Deletes the listed slash commands individually.
- Checks how many server-specific slash commands remain.
- Checks for global slash commands and warns if any are still registered.

## What it does not do

The utility does not:

- Delete global slash commands.
- Remove commands belonging to other bots.
- Delete user or message context-menu commands.
- Remove the bot from the server.
- Modify the bot’s source code or command-registration configuration.

It clears command registrations, not the underlying command implementation.

## How to use

### 1. Launch the utility

Open:

```text
ClearSlashCommands.exe
```

If you are using the version with the final pause, the console stays open until you press Enter after completion.

### 2. Enter the bot token

At the prompt:

```text
Discord BOT token (hidden):
```

Enter the token for the bot whose commands you want to clear.

The token is not displayed while you type. The script also accepts a token prefixed with `Bot ` and removes that prefix before authenticating.

Use the token locally; do not post it in Discord, screenshots, or support messages.

### 3. Enter the server ID

At the prompt:

```text
Server ID:
```

Enter the numeric ID of the server containing the command registrations you want to remove.

### 4. Review the commands

The utility displays the application name, application ID, target server ID, and discovered slash commands.

Example:

```text
Application: My Raid Bot (123456789012345678)
Server: 987654321098765432
Server slash commands found: 3
  /raid_presets
  /raid_preset
  /viewraidlist
```

Review the application and server before continuing.

### 5. Confirm deletion

The utility asks:

```text
Type DELETE to remove these server slash commands:
```

Type exactly:

```text
DELETE
```

Any other response cancels the operation without deleting commands.

### 6. Review the results

Each successful deletion is printed:

```text
Deleted /raid_presets
Deleted /raid_preset
Deleted /viewraidlist

Server slash commands remaining: 0
```

If no server-specific slash commands are found, the utility reports:

```text
No server-specific slash commands to delete.
```

## Global-command warning

After checking the server commands, the utility also checks the bot’s global command registrations.

If it finds any, it displays a warning such as:

```text
This bot also has 4 global slash commands.
They were NOT deleted and may still appear.
```

This means that clearing the server-specific commands may not remove every command you see for that bot. This version intentionally leaves global registrations untouched.

## Error handling

The supplied script:

- Rejects an empty token or a nonnumeric server ID.
- Uses a 30-second timeout for each API request.
- Retries rate-limited requests up to five attempts.
- Waits for Discord’s reported retry interval before retrying.
- Reports unsuccessful HTTP responses.
- Reports request and response-parsing errors.
- Closes its HTTP session when finished.

### Partial deletion

Deletion is not an all-or-nothing operation. Commands are deleted individually.

If an error occurs after some commands have been deleted, those successful deletions are not undone. Review the console output before running the utility again.

## Token handling

In the supplied script, the token:

- Is entered at runtime.
- Is read using `getpass`.
- Is used to authenticate requests to Discord.
- Is not explicitly written to a configuration file or printed to the console.

The executable should be built without a hardcoded token.

## Distribution

The packaged version is named:

```text
ClearSlashCommands.exe
```

The source version is named:

```text
clear_slash_commands.py
```

The utility’s purpose is narrowly scoped: select one bot and one server, review the registered server slash commands, and explicitly confirm their removal.
