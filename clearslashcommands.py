
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

import requests  # type: ignore[import-not-found]

BASE_URL = "https://discord.com/api/v10"
LOG_FILE_NAME = "slash_cleaner_logs.txt"


def get_run_directory() -> Path:
    """
    Returns the directory containing the launched EXE when compiled,
    or the directory containing this Python script when run as source.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


LOG_FILE_PATH = get_run_directory() / LOG_FILE_NAME


def log_event(message: str) -> None:
    """
    Appends an audit entry to slash_cleaner_logs.txt.

    The file is created automatically if it does not already exist.
    Never pass the bot token into this function.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with LOG_FILE_PATH.open(
            "a",
            encoding="utf-8",
        ) as log_file:
            log_file.write(f"[{timestamp}] {message}\n")

    except OSError as error:
        # Do not stop command cleanup just because the local log failed.
        print(f"Warning: Could not write log file: {error}")


def api(session: requests.Session, method: str, path: str):
    for attempt in range(1, 6):
        response = session.request(
            method,
            BASE_URL + path,
            timeout=30,
        )

        if response.status_code == 429:
            retry_after = float(
                response.json().get("retry_after", 1)
            )

            log_event(
                f"Rate limited on {method} {path}; "
                f"retrying in {retry_after:.2f} seconds "
                f"(attempt {attempt}/5)."
            )

            time.sleep(retry_after + 0.2)
            continue

        if not response.ok:
            log_event(
                f"Discord API error on {method} {path}: "
                f"HTTP {response.status_code} | {response.text}"
            )

            raise RuntimeError(
                f"Discord returned HTTP {response.status_code}: "
                f"{response.text}"
            )

        return response.json() if response.content else None

    log_event(
        f"Rate-limit retries exhausted on {method} {path}."
    )

    raise RuntimeError(
        "Rate-limit retries exhausted. Try again later."
    )


def get_slash_commands(
    session: requests.Session,
    path: str,
) -> list[dict]:
    commands = api(session, "GET", path)

    return [
        command
        for command in commands
        if command.get("type", 1) == 1
    ]


def print_commands(commands: list[dict]) -> None:
    for command in commands:
        print(f"  /{command['name']}")


def format_command_names(commands: list[dict]) -> str:
    if not commands:
        return "None"

    return ", ".join(
        f"/{command.get('name', 'unknown')}"
        for command in commands
    )


def delete_commands(
    session: requests.Session,
    path: str,
    commands: list[dict],
    scope: str,
) -> int:
    deleted_count = 0

    for command in commands:
        command_name = command.get("name", "unknown")
        command_id = command.get("id", "unknown")

        api(
            session,
            "DELETE",
            f"{path}/{command_id}",
        )

        deleted_count += 1

        print(f"Deleted /{command_name}")

        log_event(
            f"Deleted {scope} slash command: "
            f"/{command_name} | Command ID: {command_id}"
        )

    return deleted_count


def main() -> None:
    log_event("=" * 72)
    log_event("Discord Slash Command Wiper started.")

    token = getpass.getpass(
        "Discord BOT token (hidden): "
    ).strip()

    guild_id = input("Server ID: ").strip()

    if token.lower().startswith("bot "):
        token = token[4:].strip()

    if not token or not guild_id.isdigit():
        log_event(
            "Stopped: missing bot token or invalid nonnumeric server ID."
        )

        sys.exit(
            "Enter a bot token and a numeric server ID."
        )

    # Never log token contents, length, prefix, or any derivative.
    log_event(
        f"Target guild ID entered: {guild_id}"
    )

    session = requests.Session()

    session.headers.update({
        "Authorization": f"Bot {token}",
        "User-Agent": "XGC-Discord-Slash-Command-Wiper/1.1",
    })

    try:
        app = api(
            session,
            "GET",
            "/applications/@me",
        )

        app_id = app["id"]
        app_name = app["name"]

        guild_path = (
            f"/applications/{app_id}/guilds/{guild_id}/commands"
        )

        global_path = (
            f"/applications/{app_id}/commands"
        )

        log_event(
            f"Authenticated application: {app_name} | "
            f"Application ID: {app_id} | "
            f"Target Guild ID: {guild_id}"
        )

        print(f"\nApplication: {app_name} ({app_id})")
        print(f"Target server: {guild_id}")

        # ==============================================================
        # GUILD-SPECIFIC COMMANDS
        # ==============================================================

        guild_slash_commands = get_slash_commands(
            session,
            guild_path,
        )

        log_event(
            f"Found {len(guild_slash_commands)} "
            f"server slash command(s): "
            f"{format_command_names(guild_slash_commands)}"
        )

        print(
            f"\nServer slash commands found: "
            f"{len(guild_slash_commands)}"
        )

        if guild_slash_commands:
            print_commands(guild_slash_commands)

            confirmation = input(
                "\nType DELETE to remove these SERVER "
                "slash commands: "
            ).strip()

            if confirmation == "DELETE":
                log_event(
                    "Server slash command deletion confirmed."
                )

                deleted_count = delete_commands(
                    session,
                    guild_path,
                    guild_slash_commands,
                    "server",
                )

                remaining = get_slash_commands(
                    session,
                    guild_path,
                )

                print(
                    f"\nDeleted {deleted_count} server "
                    "slash command(s)."
                )

                print(
                    f"Server slash commands remaining: "
                    f"{len(remaining)}"
                )

                log_event(
                    f"Server deletion complete: "
                    f"{deleted_count} deleted; "
                    f"{len(remaining)} remaining."
                )
            else:
                print(
                    "Server command deletion cancelled. "
                    "Nothing was deleted."
                )

                log_event(
                    "Server slash command deletion cancelled "
                    "by user."
                )
        else:
            print(
                "\nNo server-specific slash commands to delete."
            )

            log_event(
                "No server-specific slash commands found."
            )

        # ==============================================================
        # GLOBAL COMMANDS
        # ==============================================================

        global_slash_commands = get_slash_commands(
            session,
            global_path,
        )

        log_event(
            f"Found {len(global_slash_commands)} "
            f"global slash command(s): "
            f"{format_command_names(global_slash_commands)}"
        )

        print(
            f"\nGlobal slash commands found: "
            f"{len(global_slash_commands)}"
        )

        if global_slash_commands:
            print_commands(global_slash_commands)

            print(
                "\nWARNING: Global command deletion affects "
                "this bot in every server where it is installed."
            )

            global_confirmation = input(
                "Type DELETE GLOBAL to remove these GLOBAL "
                "slash commands: "
            ).strip()

            if global_confirmation == "DELETE GLOBAL":
                log_event(
                    "Global slash command deletion confirmed."
                )

                deleted_count = delete_commands(
                    session,
                    global_path,
                    global_slash_commands,
                    "global",
                )

                remaining = get_slash_commands(
                    session,
                    global_path,
                )

                print(
                    f"\nDeleted {deleted_count} global "
                    "slash command(s)."
                )

                print(
                    f"Global slash commands remaining: "
                    f"{len(remaining)}"
                )

                log_event(
                    f"Global deletion complete: "
                    f"{deleted_count} deleted; "
                    f"{len(remaining)} remaining."
                )
            else:
                print(
                    "Global command deletion cancelled. "
                    "Nothing was deleted."
                )

                log_event(
                    "Global slash command deletion cancelled "
                    "by user."
                )
        else:
            print("\nNo global slash commands to delete.")

            log_event(
                "No global slash commands found."
            )

        print(
            "\nFinished. Restart your bot only after its command "
            "registration code is corrected or disabled; otherwise "
            "it may register the commands again."
        )

        log_event(
            "Discord Slash Command Wiper completed successfully."
        )

    except (
        requests.RequestException,
        RuntimeError,
        ValueError,
        KeyError,
    ) as error:
        log_event(
            f"Discord Slash Command Wiper failed: "
            f"{type(error).__name__}: {error}"
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

        log_event(
            "Discord Slash Command Wiper cancelled "
            "with Ctrl+C."
        )

    finally:
        print(f"\nLog file: {LOG_FILE_PATH}")
        input("\nPress Enter to close...")
