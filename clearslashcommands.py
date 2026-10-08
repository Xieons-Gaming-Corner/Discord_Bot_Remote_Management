# created by Xieons-Gaming-Corner
# lead developer - Xieon
# https://discord.gg/xieon - Official XGC community, and support server  
# https://github.com/xieons-gaming-corner official github of xgc 
# This tool was/is compiled, and made public located here: https://github.com/Xieons-Gaming-Corner/Discord_Slash_Command_Wiper 
# Feel free to use if it helps you, if used in any projects outside itself, please give credit to XGC, we'd appreciate it  :)


import getpass
import sys
import time

# Pylance may flag this if the package is not installed in the active venv.
# Install it with: pip install requests
import requests  # type: ignore[import-not-found]

BASE_URL = "https://discord.com/api/v10"


def main():
    token = getpass.getpass("Discord BOT token (hidden): ").strip()
    guild_id = input("Server ID: ").strip()

    if token.lower().startswith("bot "):
        token = token[4:].strip()

    if not token or not guild_id.isdigit():
        sys.exit("Enter a bot token and a numeric server ID.")

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bot {token}",
        "User-Agent": "SlashCommandCleanup/1.0",
    })

    def api(method, path):
        for _ in range(5):
            response = session.request(
                method,
                BASE_URL + path,
                timeout=30,
            )

            if response.status_code == 429:
                time.sleep(float(response.json().get("retry_after", 1)) + 0.2)
                continue

            if not response.ok:
                raise RuntimeError(
                    f"Discord returned HTTP {response.status_code}: "
                    f"{response.text}"
                )

            return response.json() if response.content else None

        raise RuntimeError("Rate-limit retries exhausted. Try again later.")

    try:
        app = api("GET", "/applications/@me")
        app_id = app["id"]

        path = f"/applications/{app_id}/guilds/{guild_id}/commands"
        commands = api("GET", path)
        slash_commands = [
            command for command in commands
            if command.get("type", 1) == 1
        ]

        print(f"\nApplication: {app['name']} ({app_id})")
        print(f"Server: {guild_id}")
        print(f"Server slash commands found: {len(slash_commands)}")

        for command in slash_commands:
            print(f"  /{command['name']}")

        if slash_commands:
            confirmation = input(
                "\nType DELETE to remove these server slash commands: "
            ).strip()

            if confirmation != "DELETE":
                print("Cancelled. Nothing was deleted.")
                return

            for command in slash_commands:
                api("DELETE", f"{path}/{command['id']}")
                print(f"Deleted /{command['name']}")

            remaining = api("GET", path)
            remaining_slash = [
                command for command in remaining
                if command.get("type", 1) == 1
            ]

            print(
                f"\nServer slash commands remaining: "
                f"{len(remaining_slash)}"
            )
        else:
            print("\nNo server-specific slash commands to delete.")

        global_commands = api(
            "GET",
            f"/applications/{app_id}/commands",
        )

        global_slash = [
            command for command in global_commands
            if command.get("type", 1) == 1
        ]

        if global_slash:
            print(
                f"\nThis bot also has {len(global_slash)} global slash "
                "commands. They were NOT deleted and may still appear."
            )

        print("\nIf Discord still displays old commands, refresh the client.")

    except (requests.RequestException, RuntimeError, ValueError) as error:
        sys.exit(f"Error: {error}")
    finally:
        session.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
    finally:
        input("\nPress Enter to close...")
