from __future__ import annotations

import importlib.metadata
import sys
import traceback

from pyallel import constants
from pyallel.colours import Colours
from pyallel.errors import InvalidExecutableErrors
from pyallel.parser import Arguments, create_parser
from pyallel.printer import Printer
from pyallel.process_group_manager import ProcessGroupManager


def main_loop(
    *args: str,
    printer: Printer,
    interactive: bool = False,
    timer: bool = False,
) -> int:
    process_group_manager = ProcessGroupManager.from_args(
        *args,
        printer=printer,
        interactive=interactive,
        timer=timer,
    )

    return process_group_manager.stream()


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

    colours = Colours.from_colour(parsed_args.colour)
    printer = Printer(colours)

    interactive = True
    if not parsed_args.interactive:
        interactive = False
    elif not constants.IN_TTY:
        interactive = False

    message = None
    try:
        exit_code = main_loop(
            *parsed_args.commands,
            printer=printer,
            interactive=interactive,
            timer=parsed_args.timer,
        )
    except InvalidExecutableErrors as e:
        exit_code = 1
        message = str(e)
    except Exception:
        exit_code = 1
        message = traceback.format_exc()

    if exit_code == 1:
        if not message:
            printer.error("Failed!")
        else:
            printer.error(f"Error: {message}")
    elif exit_code == 0:
        printer.ok("Done!")

    return exit_code


def entry_point() -> None:
    sys.exit(run(*sys.argv[1:]))


if __name__ == "__main__":
    entry_point()
