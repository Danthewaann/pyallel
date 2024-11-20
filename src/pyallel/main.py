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
from pyallel.process_group_manager import ProcessGroupManager


def main_loop(*args: str, printer: Printer, interactive: bool = False) -> int:
    process_group_manager = ProcessGroupManager.from_args(*args)

    index = 0
    exit_code = 0

    process_group_manager.run()
    if not interactive:
        printer.info("Running commands...")
        printer.info("")

        current_process = None
        while True:
            outputs = process_group_manager.stream()
            process_group_manager.outputs.merge(outputs)

            for i, output in enumerate(
                outputs.process_group_outputs[outputs.cur_process_group_id].processes
            ):
                if current_process is None:
                    current_process = output.process
                    printer.write_command_status(current_process, timer=False)
                    printer.write_output(
                        process_group_manager.outputs.process_group_outputs[
                            outputs.cur_process_group_id
                        ].processes[i]
                    )
                elif current_process is not output.process:
                    continue
                else:
                    printer.write_output(
                        outputs.process_group_outputs[
                            outputs.cur_process_group_id
                        ].processes[i]
                    )

                if output.process.poll() is not None:
                    printer.write_command_status(
                        output.process, passed=output.process.return_code() == 0
                    )
                    printer.write("", prefix=printer.prefix)
                    current_process = None

            poll = process_group_manager.poll()
            if poll is not None:
                if poll and poll > 0:
                    exit_code = poll
                    break

                process_group_manager.run()
                if process_group_manager.cur_process_group is None:
                    break
                else:
                    index += 1

            time.sleep(0.1)

    else:
        while True:
            outputs = process_group_manager.stream()
            process_group_manager.outputs.merge(outputs)

            printer.clear()
            printer.write_outputs(
                process_group_manager.outputs,
                interrupt_count=process_group_manager.interrupt_count,
            )

            poll = process_group_manager.poll()
            if poll is not None:
                if poll > 0:
                    exit_code = poll
                    break

                process_group_manager.run()
                if process_group_manager.cur_process_group is None:
                    printer.clear()
                    break
                else:
                    # printer.last_output.clear()
                    index += 1

            time.sleep(0.1)

        printer.write_outputs(
            process_group_manager.outputs,
            clear=False,
            interrupt_count=process_group_manager.interrupt_count,
        )
        printer.write("", prefix=printer.prefix)

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
    printer = Printer(colours, timer=parsed_args.timer, debug=False)

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
