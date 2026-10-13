# created by Xieons-Gaming-Corner
# lead developer - Xieon
# https://discord.gg/xieon - Official XGC community and support server
# https://github.com/Xieons-Gaming-Corner - Official XGC GitHub organization
# https://github.com/Xieons-Gaming-Corner/Discord_Slash_Command_Wiper
#
# Feel free to use this tool if it helps you. If you use code from it in
# another project, please credit Xieons-Gaming-Corner (XGC). We appreciate it.

import getpass
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests  # type: ignore[import-not-found]

BASE_URL = "https://discord.com/api/v10"
LOG_FILE_NAME = "slash_cleaner_logs.txt"
USER_AGENT = "XGC-Discord-Bot-Remote-Operations/1.4"


def get_run_directory() -> Path:
    """
    Returns the directory containing the executable when compiled, or
    the directory containing this Python source file when run normally.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


LOG_FILE_PATH = get_run_directory() / LOG_FILE_NAME


def log_event(message: str) -> None:
    """
    Appends a timestamped entry to slash_cleaner_logs.txt.

    The file is created automatically if it does not exist.
    Never pass bot tokens, OAuth tokens, or other secrets to this function.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with LOG_FILE_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
    except OSError as error:
        print(f"Warning: could not write to log file: {error}")


def api(
    session: requests.Session,
    method: str,
    path: str,
    json: Any = None,
) -> Any:
    """
    Performs an authenticated Discord API request.

    Discord HTTP 429 responses are retried up to five times. JSON can be
    supplied for POST, PUT, or PATCH requests.
    """
    for attempt in range(1, 6):
        response = session.request(
            method=method,
            url=BASE_URL + path,
            json=json,
            timeout=30,
        )

        if response.status_code == 429:
            try:
                retry_after = float(
                    response.json().get("retry_after", 1)
                )
            except (ValueError, requests.JSONDecodeError):
                retry_after = 1.0

            log_event(
                f"Rate limited: method={method}; path={path}; "
                f"retry_after={retry_after:.2f}s; "
                f"attempt={attempt}/5."
            )

            time.sleep(retry_after + 0.2)
            continue

        if not response.ok:
            log_event(
                f"Discord API error: method={method}; path={path}; "
                f"status={response.status_code}; "
                f"response={response.text}"
            )

            raise RuntimeError(
                f"Discord returned HTTP {response.status_code}: "
                f"{response.text}"
            )

        return response.json() if response.content else None

    log_event(
        f"Rate-limit retries exhausted: method={method}; path={path}."
    )

    raise RuntimeError(
        "Rate-limit retries exhausted. Try again later."
    )


def get_slash_commands(
    session: requests.Session,
    path: str,
) -> list[dict[str, Any]]:
    """
    Retrieves only chat-input/slash commands from a command collection.

    Discord command type 1 represents a CHAT_INPUT slash command.
    Context-menu commands are intentionally ignored by this function.
    """
    commands = api(session, "GET", path)

    if not isinstance(commands, list):
        raise RuntimeError(
            "Discord returned an unexpected command-list response."
        )

    return [
        command
        for command in commands
        if isinstance(command, dict)
        and command.get("type", 1) == 1
    ]


def format_command_names(
    commands: list[dict[str, Any]],
) -> str:
    """Returns slash-command names as a comma-separated log string."""
    if not commands:
        return "None"

    return ", ".join(
        f"/{command.get('name', 'unknown')}"
        for command in commands
    )


def print_commands(
    commands: list[dict[str, Any]],
) -> None:
    """Displays commands in a console-friendly list."""
    for command in commands:
        print(f"  /{command.get('name', 'unknown')}")


def delete_commands(
    session: requests.Session,
    path: str,
    commands: list[dict[str, Any]],
    scope: str,
) -> int:
    """
    Deletes each supplied command and returns the number successfully deleted.
    """
    deleted_count = 0

    for command in commands:
        command_name = str(command.get("name", "unknown"))
        command_id = str(command.get("id", ""))

        if not command_id:
            raise RuntimeError(
                f"Command /{command_name} did not include an ID."
            )

        api(
            session,
            "DELETE",
            f"{path}/{command_id}",
        )

        deleted_count += 1

        print(f"Deleted /{command_name}")

        log_event(
            f"Deleted {scope} slash command; "
            f"name=/{command_name}; command_id={command_id}."
        )

    return deleted_count


def remove_server_slash_commands(
    session: requests.Session,
    app_id: str,
    app_name: str,
) -> None:
    """
    Lists then optionally removes slash commands registered for one guild.
    """
    guild_id = input("\nServer ID: ").strip()

    if not guild_id.isdigit():
        print("Server ID must be numeric.")

        log_event(
            "Server slash-command deletion cancelled: invalid guild ID."
        )

        return

    guild_path = (
        f"/applications/{app_id}/guilds/{guild_id}/commands"
    )

    commands = get_slash_commands(session, guild_path)

    print(f"\nApplication: {app_name} ({app_id})")
    print(f"Target server: {guild_id}")
    print(f"Server slash commands found: {len(commands)}")

    log_event(
        f"Found {len(commands)} server slash command(s); "
        f"guild_id={guild_id}; "
        f"commands={format_command_names(commands)}."
    )

    if not commands:
        print("\nNo server-specific slash commands to delete.")

        log_event(
            f"No server slash commands found; guild_id={guild_id}."
        )

        return

    print_commands(commands)

    confirmation = input(
        "\nType DELETE SERVER to remove these server "
        "slash commands: "
    ).strip()

    if confirmation != "DELETE SERVER":
        print("Server command deletion cancelled. Nothing was deleted.")

        log_event(
            f"Server slash-command deletion cancelled; "
            f"guild_id={guild_id}."
        )

        return

    log_event(
        f"Server slash-command deletion confirmed; "
        f"guild_id={guild_id}."
    )

    deleted_count = delete_commands(
        session=session,
        path=guild_path,
        commands=commands,
        scope="server",
    )

    remaining_commands = get_slash_commands(session, guild_path)

    print(f"\nDeleted {deleted_count} server slash command(s).")
    print(
        f"Server slash commands remaining: "
        f"{len(remaining_commands)}"
    )

    log_event(
        f"Server slash-command deletion complete; "
        f"guild_id={guild_id}; "
        f"deleted={deleted_count}; "
        f"remaining={len(remaining_commands)}."
    )


def remove_global_slash_commands(
    session: requests.Session,
    app_id: str,
    app_name: str,
) -> None:
    """
    Lists then optionally removes every global slash command.

    Context-menu commands are not removed by this option because it targets
    only type-1 chat-input/slash commands.
    """
    global_path = f"/applications/{app_id}/commands"

    commands = get_slash_commands(session, global_path)

    print(f"\nApplication: {app_name} ({app_id})")
    print(f"Global slash commands found: {len(commands)}")

    log_event(
        f"Found {len(commands)} global slash command(s); "
        f"commands={format_command_names(commands)}."
    )

    if not commands:
        print("\nNo global slash commands to delete.")
        log_event("No global slash commands found.")
        return

    print_commands(commands)

    print(
        "\nWARNING: These global slash commands may be available in "
        "every server and user installation where your application "
        "is available."
    )

    confirmation = input(
        "Type DELETE GLOBAL to remove all listed global "
        "slash commands: "
    ).strip()

    if confirmation != "DELETE GLOBAL":
        print("Global command deletion cancelled. Nothing was deleted.")
        log_event("Global slash-command deletion cancelled.")
        return

    log_event("Global slash-command deletion confirmed.")

    deleted_count = delete_commands(
        session=session,
        path=global_path,
        commands=commands,
        scope="global",
    )

    remaining_commands = get_slash_commands(session, global_path)

    print(f"\nDeleted {deleted_count} global slash command(s).")
    print(
        f"Global slash commands remaining: "
        f"{len(remaining_commands)}"
    )

    log_event(
        f"Global slash-command deletion complete; "
        f"deleted={deleted_count}; "
        f"remaining={len(remaining_commands)}."
    )


def create_placeholder_global_command(
    session: requests.Session,
    app_id: str,
    app_name: str,
) -> None:
    """
    Replaces ALL global application commands with exactly one command:

        /placeholder

    This uses Discord's global bulk-overwrite API endpoint. It replaces
    global slash commands and global context-menu commands, not merely
    existing slash commands.
    """
    global_path = f"/applications/{app_id}/commands"

    existing_commands = api(
        session,
        "GET",
        global_path,
    )

    if not isinstance(existing_commands, list):
        raise RuntimeError(
            "Discord returned an unexpected global-command response."
        )

    print(f"\nApplication: {app_name} ({app_id})")

    print(
        "\nWARNING: This will overwrite EVERY global application command."
    )

    print(
        "This includes global slash commands, user context-menu commands, "
        "and message context-menu commands."
    )

    print(
        f"\nExisting global application commands: "
        f"{len(existing_commands)}"
    )

    if existing_commands:
        for command in existing_commands:
            command_name = str(command.get("name", "unknown"))
            command_type = command.get("type", 1)

            print(f"  {command_name} (type {command_type})")
    else:
        print("  None")

    print(
        "\nThe resulting global command list will contain only:\n"
        "  /placeholder\n"
        "  Description: This command is a placeholder and will fail\n"
    )

    print(
        "This script registers the command only. It does not add a "
        "bot or webhook interaction handler, so the command is "
        "expected to fail when invoked."
    )

    confirmation = input(
        "\nType OVERWRITE GLOBAL to replace every global command "
        "with /placeholder: "
    ).strip()

    if confirmation != "OVERWRITE GLOBAL":
        print(
            "Global command overwrite cancelled. "
            "Nothing was changed."
        )

        log_event(
            "placeholder global-command overwrite cancelled."
        )

        return

    placeholder_command = [
        {
            "name": "placeholder",
            "description": (
                "This command is a placeholder and will fail"
            ),
            "type": 1,
        }
    ]

    # PUT to this endpoint replaces the complete global command collection.
    api(
        session,
        "PUT",
        global_path,
        json=placeholder_command,
    )

    registered_commands = api(
        session,
        "GET",
        global_path,
    )

    print("\nGlobal command overwrite completed.")
    print("Registered global command: /placeholder")

    print(
        "No response handler was added, so invoking it is expected "
        "to result in a failed Discord interaction."
    )

    log_event(
        "Global application-command list overwritten with one command: "
        "/placeholder."
    )

    if isinstance(registered_commands, list):
        print(
            f"Global application commands now registered: "
            f"{len(registered_commands)}"
        )

        for command in registered_commands:
            command_name = str(command.get("name", "unknown"))
            command_type = command.get("type", 1)

            print(f"  {command_name} (type {command_type})")

        log_event(
            "Verified placeholder global-command overwrite; "
            f"command_count={len(registered_commands)}."
        )


def get_bot_guilds(
    session: requests.Session,
) -> list[dict[str, Any]]:
    """
    Returns guilds where the authenticated bot is currently a member.
    """
    guilds = api(session, "GET", "/users/@me/guilds")

    if not isinstance(guilds, list):
        raise RuntimeError(
            "Discord returned an unexpected guild-list response."
        )

    return [
        guild
        for guild in guilds
        if isinstance(guild, dict)
    ]


def view_or_leave_guilds(
    session: requests.Session,
    app_name: str,
) -> None:
    """
    Lists guilds where the bot is present and allows it to leave one
    selected guild after explicit confirmation.
    """
    guilds = get_bot_guilds(session)

    print(
        f"\n{app_name} is currently in {len(guilds)} guild(s):"
    )

    log_event(
        f"Guild inventory displayed; guild_count={len(guilds)}."
    )

    if not guilds:
        print("The bot is not currently in any guilds.")
        return

    for index, guild in enumerate(guilds, start=1):
        guild_name = str(guild.get("name", "Unknown Guild"))
        guild_id = str(guild.get("id", "Unknown ID"))

        print(
            f"  {index}. {guild_name} "
            f"(ID: {guild_id})"
        )

    print(
        "\nThis option lists the guilds where the bot is present. "
        "It does not enumerate individual members of those guilds."
    )

    selection = input(
        "\nEnter a guild number to remove the bot from it, "
        "or press Enter to return: "
    ).strip()

    if not selection:
        print("No guild selected.")
        log_event("Guild-leave menu closed without a selection.")
        return

    if not selection.isdigit():
        print("Invalid guild selection.")
        log_event(
            f"Invalid guild selection entered: {selection!r}."
        )
        return

    selected_index = int(selection)

    if selected_index < 1 or selected_index > len(guilds):
        print("That guild number is outside the displayed list.")
        log_event(
            f"Out-of-range guild selection: {selected_index}."
        )
        return

    selected_guild = guilds[selected_index - 1]
    guild_id = str(selected_guild.get("id", ""))
    guild_name = str(
        selected_guild.get("name", "Unknown Guild")
    )

    if not guild_id:
        print("The selected guild does not contain a usable guild ID.")
        log_event(
            f"Selected guild missing an ID; guild_name={guild_name}."
        )
        return

    print(
        f"\nWARNING: This will remove {app_name} from:\n"
        f"  Server: {guild_name}\n"
        f"  Guild ID: {guild_id}\n"
    )

    confirmation = input(
        "Type LEAVE GUILD to remove the bot from this server: "
    ).strip()

    if confirmation != "LEAVE GUILD":
        print("Guild leave cancelled. The bot remains in the server.")

        log_event(
            f"Guild leave cancelled; "
            f"guild_name={guild_name}; guild_id={guild_id}."
        )

        return

    api(
        session,
        "DELETE",
        f"/users/@me/guilds/{guild_id}",
    )

    print(f"The bot left: {guild_name} ({guild_id})")

    log_event(
        f"Bot left guild; "
        f"guild_name={guild_name}; guild_id={guild_id}."
    )


def display_count(
    label: str,
    value: Any,
) -> None:
    """
    Shows an application count without treating an absent API field as zero.
    """
    if isinstance(value, int):
        displayed_value = str(value)
    else:
        displayed_value = "Not returned by Discord"

    print(f"{label}: {displayed_value}")
    log_event(f"{label}: {displayed_value}.")


def view_install_statistics(
    session: requests.Session,
) -> None:
    """
    Displays aggregate install and OAuth authorization counts that Discord
    includes in the current application object.
    """
    app = api(
        session,
        "GET",
        "/applications/@me",
    )

    if not isinstance(app, dict):
        raise RuntimeError(
            "Discord returned an unexpected application response."
        )

    app_name = str(app.get("name", "Unknown Application"))
    app_id = str(app.get("id", "Unknown ID"))

    print(
        "\nApplication Installation / Authorization Statistics"
    )
    print("-" * 56)
    print(f"Application: {app_name} ({app_id})")

    display_count(
        "Approximate server installs",
        app.get("approximate_guild_count"),
    )

    display_count(
        "Approximate individual-user installs",
        app.get("approximate_user_install_count"),
    )

    display_count(
        "Approximate individual-user OAuth authorizations",
        app.get("approximate_user_authorization_count"),
    )

    print(
        "\nDiscord provides aggregate counts only. A bot token does "
        "not return the identities of individual users who installed "
        "or authorized the application. A bot token also cannot "
        "globally revoke another user's OAuth authorization."
    )

    log_event(
        f"Application statistics displayed; "
        f"application_id={app_id}."
    )


def show_menu() -> str:
    """Prints the main menu and returns the entered operation number."""
    print(
        "\n" + "=" * 64 + "\n"
        "Discord Bot Remote Operations\n"
        "=" * 64 + "\n"
        "What bot remote operation do you want to do?\n\n"
        "  1. Remove server-specific slash commands\n"
        "  2. Remove global slash commands\n"
        "  3. Create /placeholder and overwrite global commands\n"
        "  4. View guilds / remove the bot from a selected guild\n"
        "  5. View application install / authorization statistics\n"
        "  6. Exit\n"
    )

    return input("Select a number: ").strip()


def main() -> None:
    """
    Prompts for a bot token, confirms it through Discord's API, then starts
    the local remote-operations menu.
    """
    log_event("=" * 72)
    log_event("Discord Bot Remote Operations started.")

    token = getpass.getpass(
        "Discord BOT token (hidden): "
    ).strip()

    if token.lower().startswith("bot "):
        token = token[4:].strip()

    if not token:
        log_event("Stopped: no bot token was entered.")
        sys.exit("Enter a bot token.")

    # The token is deliberately never logged.
    session = requests.Session()

    session.headers.update({
        "Authorization": f"Bot {token}",
        "User-Agent": USER_AGENT,
    })

    try:
        app = api(
            session,
            "GET",
            "/applications/@me",
        )

        if not isinstance(app, dict):
            raise RuntimeError(
                "Discord returned an unexpected application response."
            )

        app_id = str(app.get("id", ""))
        app_name = str(app.get("name", "Unknown Application"))

        if not app_id:
            raise RuntimeError(
                "Discord did not return an application ID."
            )

        print(
            f"\nAuthenticated application: "
            f"{app_name} ({app_id})"
        )

        log_event(
            f"Authenticated application; "
            f"name={app_name}; application_id={app_id}."
        )

        while True:
            choice = show_menu()

            if choice == "1":
                remove_server_slash_commands(
                    session=session,
                    app_id=app_id,
                    app_name=app_name,
                )

            elif choice == "2":
                remove_global_slash_commands(
                    session=session,
                    app_id=app_id,
                    app_name=app_name,
                )

            elif choice == "3":
                create_placeholder_global_command(
                    session=session,
                    app_id=app_id,
                    app_name=app_name,
                )

            elif choice == "4":
                view_or_leave_guilds(
                    session=session,
                    app_name=app_name,
                )

            elif choice == "5":
                view_install_statistics(session)

            elif choice == "6":
                print("\nExiting.")
                log_event("User selected Exit from main menu.")
                return

            else:
                print(
                    "\nInvalid selection. Enter a number from 1 to 6."
                )

                log_event(
                    f"Invalid main-menu selection: {choice!r}."
                )

    except (
        requests.RequestException,
        RuntimeError,
        ValueError,
        KeyError,
    ) as error:
        log_event(
            f"Tool error: {type(error).__name__}: {error}"
        )

        sys.exit(f"Error: {error}")

    finally:
        session.close()
        log_event("HTTP session closed.")


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\nCancelled.")
        log_event("Tool cancelled with Ctrl+C.")

    finally:
        print(f"\nLog file: {LOG_FILE_PATH}")
        input("\nPress Enter to close...")
