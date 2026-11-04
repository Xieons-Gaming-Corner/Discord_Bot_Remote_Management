# created by Xieons-Gaming-Corner
# lead developer - Xieon
# https://discord.gg/xieon - Official XGC community and support server
# https://github.com/Xieons-Gaming-Corner - Official XGC GitHub organization
# https://github.com/Xieons-Gaming-Corner/Discord_Slash_Command_Wiper
#
# Feel free to use this tool if it helps you. If you use code from it in
# another project, please credit Xieons-Gaming-Corner (XGC). We appreciate it.

import getpass
import math
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

import requests


BASE_URL = "https://discord.com/api/v10"
VERSION = "1.2"
LOG_FILE_NAME = "slash_cleaner_logs.txt"
REQUEST_TIMEOUT = (10, 30)
MAX_ATTEMPTS = 5
MAX_RATE_LIMIT_WAIT = 300.0


class ToolError(Exception):
    """An error whose message is safe to display and log."""


def get_run_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


LOG_FILE_PATH = get_run_directory() / LOG_FILE_NAME


def log_event(message: str) -> None:
    """Append an audit entry. Never pass credentials to this function."""
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")

    # Keep each audit entry on one line.
    safe_message = str(message).replace("\r", "\\r").replace("\n", "\\n")

    try:
        with LOG_FILE_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {safe_message}\n")
    except OSError:
        print("Warning: Could not write to the local log file.")


def read_token() -> str:
    try:
        # Refuse input if getpass cannot hide it in this environment.
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            token = getpass.getpass("Discord BOT token (hidden): ").strip()
    except getpass.GetPassWarning:
        raise ToolError(
            "Hidden token input is unavailable. "
            "Run this tool in a normal terminal or console."
        ) from None

    if token.lower().startswith("bot "):
        token = token[4:].strip()

    if not token or any(character.isspace() for character in token):
        raise ToolError("Enter a nonempty bot token without whitespace.")

    return token


def read_guild_id() -> str:
    value = input("Server ID: ").strip()

    if (
        not value
        or not value.isascii()
        or not value.isdecimal()
        or len(value) > 20
        or not 0 < int(value) < 2**64
    ):
        raise ToolError("Enter a valid numeric Discord server ID.")

    return str(int(value))


def get_retry_delay(response: requests.Response) -> float:
    value = None

    try:
        payload = response.json()
        if isinstance(payload, dict):
            value = payload.get("retry_after")
    except ValueError:
        pass

    if value is None:
        value = response.headers.get("Retry-After")

    try:
        delay = float(value)
    except (TypeError, ValueError):
        raise ToolError(
            "Discord returned a rate limit without a valid retry delay. "
            "Stop and try again later."
        ) from None

    if not math.isfinite(delay) or delay < 0:
        raise ToolError("Discord returned an invalid rate-limit delay.")

    if delay > MAX_RATE_LIMIT_WAIT:
        raise ToolError(
            f"Discord requested a wait of {delay:.1f} seconds. "
            "Stop and try again later."
        )

    return delay + 0.25


def api(session: requests.Session, method: str, path: str):
    if method not in ("GET", "DELETE") or not path.startswith("/applications/"):
        raise ToolError("Blocked an unexpected API request.")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = session.request(
                method,
                BASE_URL + path,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=False,
            )
        except requests.RequestException as error:
            # Do not log raw exception text or request objects.
            log_event(
                f"Network failure: {method} {path} | "
                f"Error type: {type(error).__name__}"
            )
            raise ToolError(
                "The Discord request failed. Check your connection. "
                "If this happened during deletion, some commands may "
                "already have been removed; rerun to inspect the remainder."
            ) from None

        with response:
            status = response.status_code

            if status == 429:
                if attempt == MAX_ATTEMPTS:
                    raise ToolError(
                        "Rate-limit retries exhausted. Try again later."
                    )

                delay = get_retry_delay(response)

                print(f"Rate limited; waiting {delay:.2f} seconds...")
                log_event(
                    f"Rate limited: {method} {path} | "
                    f"Wait: {delay:.2f}s | Attempt: {attempt}/{MAX_ATTEMPTS}"
                )
                time.sleep(delay)
                continue

            if not 200 <= status < 300:
                # Deliberately omit response bodies and headers.
                log_event(f"Discord API error: {method} {path} | HTTP {status}")

                explanations = {
                    401: "Authentication failed. Check the bot token.",
                    403: (
                        "Discord denied this request. Check the application, "
                        "server ID, and access."
                    ),
                    404: (
                        "The requested resource was not found. Check the "
                        "server ID; a command may also have been removed "
                        "by another process."
                    ),
                }

                if 300 <= status < 400:
                    explanation = "An unexpected redirect was blocked."
                elif status >= 500:
                    explanation = (
                        "Discord reported a server error. Try again later."
                    )
                else:
                    explanation = explanations.get(
                        status,
                        "Discord rejected the request.",
                    )

                raise ToolError(f"HTTP {status}: {explanation}")

            if status == 204 or not response.content:
                return None

            try:
                return response.json()
            except ValueError:
                raise ToolError(
                    "Discord returned an unexpected non-JSON response."
                ) from None

    raise ToolError("The request could not be completed.")


def get_slash_commands(
    session: requests.Session,
    path: str,
) -> list[dict]:
    payload = api(session, "GET", path)

    if not isinstance(payload, list):
        raise ToolError("Discord returned an unexpected command-list format.")

    commands = []

    for command in payload:
        if not isinstance(command, dict):
            raise ToolError("Discord returned an invalid command entry.")

        if command.get("type", 1) != 1:
            continue

        command_id = command.get("id")
        name = command.get("name")

        if (
            not isinstance(command_id, str)
            or not command_id.isascii()
            or not command_id.isdecimal()
            or not isinstance(name, str)
            or not name
        ):
            raise ToolError("Discord returned invalid slash-command data.")

        commands.append(command)

    return sorted(commands, key=lambda command: command["name"].casefold())


def format_command_names(commands: list[dict]) -> str:
    return ", ".join(f"/{command['name']}" for command in commands) or "None"


def delete_commands(
    session: requests.Session,
    path: str,
    commands: list[dict],
    scope: str,
) -> int:
    deleted_count = 0

    try:
        for command in commands:
            api(session, "DELETE", f"{path}/{command['id']}")
            deleted_count += 1

            print(f"Deleted /{command['name']}")
            log_event(
                f"Deleted {scope} slash command: /{command['name']} | "
                f"Command ID: {command['id']}"
            )
    finally:
        # Also records partial progress if a request fails or is interrupted.
        log_event(
            f"{scope.title()} deletion progress: "
            f"{deleted_count}/{len(commands)} confirmed deleted."
        )

    return deleted_count


def process_scope(
    session: requests.Session,
    path: str,
    scope: str,
    confirmation_text: str,
) -> None:
    commands = get_slash_commands(session, path)

    print(f"\n{scope.title()} slash commands found: {len(commands)}")

    log_event(
        f"Found {len(commands)} {scope} slash command(s): "
        f"{format_command_names(commands)}"
    )

    if not commands:
        print("Nothing to delete in this scope.")
        return

    for command in commands:
        print(f"  /{command['name']} | ID: {command['id']}")

    if scope == "global":
        print(
            "\nWARNING: Deleting global commands affects this application's "
            "global commands everywhere they are available, not just "
            "the server entered above."
        )

    print(
        "\nOnly the listed slash commands will be deleted. "
        "User/message context-menu commands are not targeted."
    )

    confirmation = input(
        f"\nType {confirmation_text} to delete these "
        f"{scope.upper()} slash commands "
        "(anything else cancels this scope): "
    ).strip()

    if confirmation != confirmation_text:
        print(f"{scope.title()} deletion cancelled. Nothing deleted here.")
        log_event(f"{scope.title()} deletion cancelled by user.")
        return

    log_event(
        f"{scope.title()} deletion confirmed for {len(commands)} commands."
    )

    deleted_count = delete_commands(session, path, commands, scope)
    remaining = get_slash_commands(session, path)

    print(f"\nConfirmed deleted: {deleted_count}")
    print(f"{scope.title()} slash commands remaining: {len(remaining)}")

    log_event(
        f"{scope.title()} deletion complete: {deleted_count} deleted; "
        f"{len(remaining)} remaining."
    )

    if remaining:
        print(
            "Some commands remain or were registered again. "
            "Check whether the bot is still syncing commands."
        )


def main() -> int:
    log_event("=" * 72)
    log_event(f"Discord Slash Command Wiper {VERSION} started.")

    print(f"XGC Discord Slash Command Wiper v{VERSION}")
    print("Run only for a bot/application you own or are authorized to manage.")
    print(
        "Stop automatic command syncing before continuing, "
        "or deleted commands may return."
    )
    print(
        "This tool handles your token locally and sends API requests "
        "to Discord. Do not share your token or paste it into support chat.\n"
    )

    session = None

    try:
        token = read_token()
        guild_id = read_guild_id()

        session = requests.Session()

        # Ignore implicit environment proxies, netrc authentication,
        # and environment CA overrides. Default TLS verification stays on.
        session.trust_env = False
        session.headers.update({
            "Authorization": f"Bot {token}",
            "User-Agent": f"XGC-Discord-Slash-Command-Wiper/{VERSION}",
        })

        # Remove this local reference; the session still needs its header.
        # This is not a guarantee of secure memory erasure.
        del token

        app = api(session, "GET", "/applications/@me")

        if not isinstance(app, dict):
            raise ToolError("Discord returned an invalid application response.")

        app_id = app.get("id")
        app_name = app.get("name")

        if (
            not isinstance(app_id, str)
            or not app_id.isascii()
            or not app_id.isdecimal()
            or not isinstance(app_name, str)
            or not app_name
        ):
            raise ToolError("Discord returned invalid application details.")

        print(f"\nApplication: {app_name} ({app_id})")
        print(f"Target server: {guild_id}")
        print(
            "Verify these details before confirming any deletion. "
            "Global deletion is not limited to this server."
        )

        log_event(
            f"Authenticated application: {app_name} | "
            f"Application ID: {app_id} | Target Guild ID: {guild_id}"
        )

        process_scope(
            session,
            f"/applications/{app_id}/guilds/{guild_id}/commands",
            "server",
            "DELETE",
        )

        process_scope(
            session,
            f"/applications/{app_id}/commands",
            "global",
            "DELETE GLOBAL",
        )

        print(
            "\nFinished. Restart your bot only after its command-registration "
            "code is corrected or disabled; otherwise it may register "
            "the commands again."
        )

        log_event("Discord Slash Command Wiper completed successfully.")
        return 0

    except (KeyboardInterrupt, EOFError):
        print(
            "\nCancelled. Any deletions already completed remain in effect."
        )
        log_event("Cancelled or input stream closed.")
        return 130

    except ToolError as error:
        print(f"\nError: {error}")
        print(
            "If deletion had started, it may be partially complete. "
            "Review the log and rerun to inspect remaining commands."
        )
        log_event(f"Stopped: {error}")
        return 1

    except Exception as error:
        # Avoid printing arbitrary exception contents that could hold secrets.
        print(
            "\nAn unexpected error occurred. "
            f"Error type: {type(error).__name__}. "
            "Review the code locally; do not share credentials."
        )
        log_event(f"Unexpected failure: {type(error).__name__}")
        return 1

    finally:
        if session is not None:
            session.headers.pop("Authorization", None)
            session.cookies.clear()
            session.close()
            log_event("HTTP session closed.")


if __name__ == "__main__":
    exit_code = main()

    print(f"\nLog file: {LOG_FILE_PATH}")

    if sys.stdin.isatty():
        try:
            input("\nPress Enter to close...")
        except (KeyboardInterrupt, EOFError):
            pass

    sys.exit(exit_code)
