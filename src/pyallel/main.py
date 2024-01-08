from __future__ import annotations

import sys
import time
import importlib.metadata

from pyallel.parser import Arguments, create_parser
from pyallel.process import ProcessGroup, format_time_taken
from pyallel import constants


def main_loop(
    commands: list[str],
    fail_fast: bool = False,
    interactive: bool = False,
    debug: bool = False,
    stream: bool = False,
) -> bool:
    process_group = ProcessGroup.from_commands(
        commands, interactive=interactive, fail_fast=fail_fast, debug=debug
    )
    if not stream:
        return process_group.run()

    return process_group.stream()


def run(*args: str) -> int:
    parser = create_parser()
    parsed_args = parser.parse_args(args=args, namespace=Arguments())

    if parsed_args.version:
        my_version = importlib.metadata.version("pyallel")
        print(my_version)
        return 0

    if parsed_args.verbose:
        print(parsed_args)

    if not parsed_args.commands:
        parser.print_help()
        return 2

    start = time.perf_counter()

    exit_code = 0
    message = None
    try:
        status = main_loop(
            parsed_args.commands,
            parsed_args.fail_fast,
            parsed_args.interactive,
            parsed_args.debug,
            parsed_args.stream,
        )
    except Exception as e:
        status = False
        message = str(e)

    if not status:
        if not message:
            print(f"{constants.RED_BOLD}A command failed!{constants.NC}")
        else:
            print(f"{constants.RED_BOLD}Error: {message}{constants.NC}")
        exit_code = 1
    else:
        print(f"{constants.GREEN_BOLD}Success!{constants.NC}")

    if parsed_args.debug:
        elapsed = time.perf_counter() - start
        print(f"\nTime taken : {format_time_taken(elapsed)}")

    return exit_code


def entry_point() -> None:
    sys.exit(run(*sys.argv[1:]))


if __name__ == "__main__":
    entry_point()
