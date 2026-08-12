from __future__ import annotations

import importlib.metadata
import logging
import sys
import time
import traceback

from pyallel import constants
from pyallel.colours import Colours
from pyallel.errors import PyallelError
from pyallel.logging import configure_logging
from pyallel.parser import Arguments, create_parser
from pyallel.printer import (
    InteractiveConsolePrinter,
    NonInteractiveConsolePrinter,
    Printer,
    generate_summary,
)
from pyallel.process_group_manager import ProcessGroupManager

logger = logging.getLogger(__name__)


def entry_point(*args: str) -> int:
    args = args or tuple(sys.argv[1:])
    parser = create_parser()
    parsed_args = parser.parse_args(args=args, namespace=Arguments())

    if parsed_args.version:
        my_version = importlib.metadata.version("pyallel")
        print(my_version)
        return 0

    if not parsed_args.commands:
        parser.print_help()
        return 2

    configure_logging(debug=parsed_args.debug)

    colours = Colours.from_colour(parsed_args.colour)
    printer: Printer
    if not parsed_args.interactive or not constants.IN_TTY:
        printer = NonInteractiveConsolePrinter(colours, timer=parsed_args.timer)
    else:
        printer = InteractiveConsolePrinter(colours, timer=parsed_args.timer)

    try:
        process_group_manager = ProcessGroupManager.from_args(*parsed_args.commands)
    except PyallelError as e:
        print(f"{colours.red_bold}Error{colours.reset_colour}: {e!s}")
        return 1

    logger.debug("starting run with arguments:\n%s", parsed_args)
    try:
        exit_code = run(process_group_manager, printer)
    except Exception:
        logger.exception("failed run with arguments:\n%s", parsed_args)
        print(
            f"{colours.red_bold}Error{colours.reset_colour}: encountered unexpected error\n\n{traceback.format_exc()}"
        )
        return 1

    if exit_code == 1:
        logger.error("failed run with arguments:\n%s", parsed_args)
    else:
        logger.debug("finished run with arguments:\n%s", parsed_args)

    if parsed_args.summary:
        print()
        outputs = [group.stream() for group in process_group_manager.groups]
        summary = generate_summary(process_group_outputs=outputs, colours=colours, include_timer=parsed_args.timer)
        print("\n".join(summary))

    return exit_code


def run(process_group_manager: ProcessGroupManager, printer: Printer) -> int:
    process_group_manager.run()
    while True:
        output = process_group_manager.stream()
        printer.print(output)

        poll = process_group_manager.poll()
        if poll is not None:
            # If we still have new output to print after the process group has completed,
            # make sure to print it here before continuing
            output = process_group_manager.stream()
            printer.print(output, done=True)

            if poll > 0:
                return poll

            process_group_manager.run()
            if not process_group_manager.next():
                return 0

        time.sleep(0.008)


if __name__ == "__main__":
    sys.exit(entry_point())
