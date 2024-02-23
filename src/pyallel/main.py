from __future__ import annotations

import sys
import traceback
import importlib.metadata
from pyallel.errors import InvalidExecutableErrors

from pyallel.parser import Arguments, create_parser
from pyallel.process import ProcessGroup
from pyallel import constants


def main_loop(
    *commands: str,
    interactive: bool = False,
    timer: bool = False,
    verbose: bool = False,
) -> int:
    process_group = ProcessGroup.from_commands(
        *commands, interactive=interactive, timer=timer, verbose=verbose
    )

    return process_group.stream()


def run(*args: str) -> int:
    parser = create_parser()
    parsed_args = parser.parse_args(args=args, namespace=Arguments())

    if parsed_args.version:
        my_version = importlib.metadata.version("pyallel")
        print(my_version)
        return 0

    if not parsed_args.commands:
        parser.print_help()
        return 2

    message = None
    try:
        exit_code = main_loop(
            *parsed_args.commands,
            interactive=parsed_args.interactive,
            timer=parsed_args.timer,
            verbose=parsed_args.verbose,
        )
    except InvalidExecutableErrors as e:
        exit_code = 1
        message = str(e)
    except Exception:
        exit_code = 1
        message = traceback.format_exc()

    if exit_code == 1:
        if not message:
            print(f"{constants.RED_BOLD}A command failed!{constants.RESET_COLOUR}")
        else:
            print(f"{constants.RED_BOLD}Error: {message}{constants.RESET_COLOUR}")
    elif exit_code == 0:
        print(f"{constants.GREEN_BOLD}Success!{constants.RESET_COLOUR}")

    return exit_code


def entry_point() -> None:
    sys.exit(run(*sys.argv[1:]))


if __name__ == "__main__":
    entry_point()
