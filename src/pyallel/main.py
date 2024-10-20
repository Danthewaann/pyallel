from __future__ import annotations

import importlib.metadata
import sys
import traceback
import time

from pyallel import constants
from pyallel.colours import Colours
from pyallel.errors import InvalidExecutableErrors
from pyallel.parser import Arguments, create_parser
from pyallel.printer import Printer
from pyallel.process_group import Output
from pyallel.process_group_manager import ProcessGroupManager


def main_loop(*args: str, printer: Printer, interactive: bool = False) -> int:
    process_group_manager = ProcessGroupManager.from_args(*args)

    if not interactive:
        printer.info("Running commands...")
        printer.info("")

    all_output: list[list[Output]] = [[] for _ in process_group_manager.process_groups]
    index = 0
    exit_code = 0
    process_group_manager.run()
    while True:
        outputs = process_group_manager.stream()
        for i, output in enumerate(outputs):
            if len(all_output[index]) < i + 1:
                all_output[index].append(Output(process=output.process, data=output.data))
            else:
                all_output[index][i].data += output.data

        printer.write_outputs(all_output, exit_code=process_group_manager.exit_code, interrupt_count=process_group_manager.interrupt_count)

        poll = process_group_manager.poll()
        if poll is not None:
            if process_group_manager.exit_code:
                exit_code = process_group_manager.exit_code
                break

            if poll > 0:
                exit_code = poll

            process_group_manager.run()
            if process_group_manager.cur_process_group is None:
                break
            else:
                index += 1

        time.sleep(0.1)

    printer.write_outputs(all_output, clear=False, exit_code=process_group_manager.exit_code, interrupt_count=process_group_manager.interrupt_count)

    return exit_code


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
        exit_code = main_loop(
            *parsed_args.commands, printer=printer, interactive=interactive
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
