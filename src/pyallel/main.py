from __future__ import annotations

import importlib.metadata
import sys
import traceback
import time

from pyallel import constants
from pyallel.colours import Colours
from pyallel.errors import InvalidLinesModifierError
from pyallel.parser import Arguments, create_parser
from pyallel.printer import Printer
from pyallel.process_group_manager import ProcessGroupManager


def run_interactive(
    process_group_manager: ProcessGroupManager, printer: Printer
) -> int:
    while True:
        process_group_manager.stream()

        printer.clear_printed_lines()
        output = process_group_manager.get_cur_process_group_output()
        printer.print_progress_group_output(
            output, process_group_manager._interrupt_count
        )

        poll = process_group_manager.poll()
        if poll is not None:
            printer.clear_printed_lines()
            printer.print_progress_group_output(
                output, process_group_manager._interrupt_count, tail_output=False
            )

            if poll > 0:
                return poll

            printer.reset()
            process_group_manager.run()
            if not process_group_manager.next():
                return 0

        time.sleep(0.1)


def run_non_interactive(
    process_group_manager: ProcessGroupManager, printer: Printer
) -> int:
    current_process = None

    while True:
        outputs = process_group_manager.stream()

        for pg in outputs.process_group_outputs.values():
            for output in pg.processes:
                if current_process is None:
                    current_process = output.process
                    output = process_group_manager.get_process(output.id)
                    printer.print_process_output(
                        output, include_progress=False, include_timer=False
                    )
                elif current_process is not output.process:
                    continue
                else:
                    printer.print_process_output(output, include_cmd=False)

                if output.process.poll() is not None:
                    printer.print_process_output(output, include_output=False)
                    current_process = None

        poll = process_group_manager.poll()
        if poll is not None:
            if poll > 0:
                return poll

            process_group_manager.run()
            if not process_group_manager.next():
                return 0

        time.sleep(0.1)


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
    printer = Printer(colours, timer=parsed_args.timer)

    interactive = True
    if not parsed_args.interactive:
        interactive = False
    elif not constants.IN_TTY:
        interactive = False

    message = None
    try:
        process_group_manager = ProcessGroupManager.from_args(*parsed_args.commands)
        process_group_manager.run()

        if interactive:
            exit_code = run_interactive(process_group_manager, printer)
        else:
            exit_code = run_non_interactive(process_group_manager, printer)
    except InvalidLinesModifierError as e:
        exit_code = 1
        message = str(e)
    except Exception:
        exit_code = 1
        message = traceback.format_exc()

    if exit_code == 1:
        if not message:
            printer.error("\nFailed!")
        else:
            printer.error(f"Error: {message}")
    elif exit_code == 0:
        printer.ok("\nDone!")

    return exit_code


def entry_point() -> None:
    sys.exit(run(*sys.argv[1:]))


if __name__ == "__main__":
    entry_point()
