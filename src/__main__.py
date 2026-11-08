"""Command-line entry point for the RageAgainstMachine application."""

import sys

from src.core.utils import Logger


def validate_commands_args() -> None:
    """Validate the command-line arguments.

    Ensure that the provided command is one of the supported commands.
    If no command is provided or an invalid command is specified,
    log an error message and terminate the application.

    Raises:
        SystemExit: If the command is missing or invalid.
    """
    allowed_commands: set[str] = {
        "search",
        "evaluate",
        "search_dataset",
        "answer",
        "answer_dataset",
        "index"
    }
    if len(sys.argv) < 2 or sys.argv[1] not in allowed_commands:
        Logger.error(
            f"Invalid command. Allowed commands: {allowed_commands}",
            "Invalid Commands"
        )
        sys.exit(1)

# View current limit (typically 1000)

# Increase the recursion limit

def main() -> None:
    """Initialize Django and execute the CLI application.

    Configure the Django settings module, initialize the Django
    application, validate the command-line arguments, and invoke
    the RageAgainstMachine CLI using Python Fire.
    """
    import os
    from typing import cast

    from fire import Fire
    sys.setrecursionlimit(5000)

    _ = os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "src.server.config.settings"
    )

    import django
    django.setup()

    from src.core.rage_against_machine import RageAgainstMachine

    validate_commands_args()

    _: object = cast(object, Fire(RageAgainstMachine))


if __name__ == "__main__":
    main()
