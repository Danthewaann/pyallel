from __future__ import annotations

import sys
import time
import importlib.metadata

from pyallel.errors import InvalidExecutableErrors, InvalidExecutableError
from pyallel.parser import Arguments, create_parser
from pyallel.process import Process
from concurrent.futures import ThreadPoolExecutor

IN_TTY = sys.__stdin__.isatty()

if IN_TTY:
    WHITE_BOLD = "\033[1m"
    GREEN_BOLD = "\033[1;32m"
    BLUE_BOLD = "\033[1;34m"
    RED_BOLD = "\033[1;31m"
    CLEAR_LINE = "\033[2K"
    CLEAR_SCREEN = "\033[2J"
    SAVE_CURSOR = "\033[s"
    RESTORE_CURSOR = "\033[u"
    UP_LINE = "\033[1F"
    NC = "\033[0m"
    CR = "\r"
else:
    WHITE_BOLD = ""
    GREEN_BOLD = ""
    BLUE_BOLD = ""
    RED_BOLD = ""
    CLEAR_LINE = ""
    CLEAR_SCREEN = ""
    SAVE_CURSOR = ""
    RESTORE_CURSOR = ""
    UP_LINE = ""
    NC = ""
    CR = ""


ICONS = ("/", "-", "\\", "|")
# Unicode character bytes to render different symbols in the terminal
TICK = "\u2713"
X = "\u2717"


def create_processes(commands: list[str]) -> list[Process]:
    processes: list[Process] = []
    errors: list[InvalidExecutableError] = []

    for command in commands:
        try:
            processes.append(Process.from_command(command))
        except InvalidExecutableError as e:
            errors.append(e)

    if errors:
        raise InvalidExecutableErrors(*errors)

    return processes


def indent(output: str) -> str:
    return "\n".join("    " + line for line in output.splitlines())


def format_time_taken(time_taken: float) -> str:
    seconds = int(time_taken) % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    msg = ""
    if time_taken < 60:
        msg = f"{seconds}s"
    elif 60 <= time_taken < 3600:
        msg = f"{minutes}m"
        if seconds:
            msg += f" {seconds}s"
    elif time_taken >= 3600:
        msg = f"{hour}h"
        if minutes:
            msg += f" {minutes}m"
        if seconds:
            msg += f" {seconds}s"

    return msg


def print_command_status(process: Process, passed: bool, debug: bool = False) -> None:
    colour = RED_BOLD
    msg = "failed"
    icon = X
    if passed:
        colour = GREEN_BOLD
        msg = "done"
        icon = TICK

    print(f"[{BLUE_BOLD}{process.name}", end="")

    if debug:
        print(f" {' '.join(process.args)}", end="")

    print(f"{NC}]{colour} {msg} ", end="")

    if debug:
        elapsed = time.perf_counter() - process.start
        print(f"in {format_time_taken(elapsed)} ", end="")

    print(f"{icon}{NC}")


def print_command_output(process: Process) -> None:
    output = process.stdout().read()
    if output:
        print(f"{indent(output.decode())}")
    print()


def main_loop(
    commands: list[str],
    fail_fast: bool = False,
    interactive: bool = False,
    debug: bool = False,
    stream: bool = False,
) -> bool:
    if not stream:
        return non_streamed_mode(commands, fail_fast, interactive, debug)

    return streamed_mode(commands, fail_fast, interactive, debug)


def streamed_mode(
    commands: list[str],
    fail_fast: bool = False,
    interactive: bool = False,
    debug: bool = False,
) -> bool:
    processes = create_processes(commands)

    for process in processes:
        process.run()

    completed_processes: set[str] = set()
    passed = True

    while True:
        for process in processes:
            print(f"[{process.name}] running...")
            if process.output:
                print(indent(process.output.decode()))

        with ThreadPoolExecutor(max_workers=1) as executor:
            for process in processes:
                if process.name in completed_processes:
                    continue

                if process.poll() is not None:
                    completed_processes.add(process.name)

                executor.submit(process.readline)

        lines = sum(len(process.output.splitlines()) for process in processes)
        print(lines)
        # for line in range(lines):
        #     print(f"{CLEAR_LINE}\033[1F", end="")

        # lines = sum(len(process.output.splitlines()) for process in processes)
        # print(f"\033[{lines +1}F{CLEAR_LINE}", end="")

        for process in processes:
            print(f"[{process.name}] running...")
            if process.output:
                print(indent(process.output.decode()))

        if len(completed_processes) == len(processes):
            break

        # print(f"\033[{lines +1}F{CLEAR_LINE}", end="")
        lines = sum(len(process.output.splitlines()) for process in processes)
        print(lines)
        # for line in range(lines + 2):
        #     print(f"{CLEAR_LINE}\033[1F", end="")

        # old_command_output = command_output
        # print(f"{RESTORE_CURSOR}", end="")
        # print("\033]0J", end="")
        # print(f"{SAVE_CURSOR}", end="")
        # print(f"{CLEAR_SCREEN}", end="")
        # for _ in command_output.splitlines():
        #     print(f"{UP_LINE}{CLEAR_LINE}{CR}", end="")

    return passed


def non_streamed_mode(
    commands: list[str],
    fail_fast: bool = False,
    interactive: bool = False,
    debug: bool = False,
) -> bool:
    processes = create_processes(commands)

    for process in processes:
        process.run()

    completed_processes: set[str] = set()
    passed = True

    if not interactive or not IN_TTY:
        print(f"{WHITE_BOLD}Running commands...{NC}\n")

    while True:
        if interactive and IN_TTY:
            for icon in ICONS:
                print(
                    f"{CLEAR_LINE}{CR}{WHITE_BOLD}Running commands{NC} {icon}", end=""
                )
                time.sleep(0.1)

        for process in processes:
            if process.name in completed_processes or process.poll() is None:
                continue

            completed_processes.add(process.name)
            passed = run_process(process, debug=debug)
            if fail_fast and not passed:
                return False

        if len(completed_processes) == len(processes):
            break

    return passed


def run_process(process: Process, debug: bool = False) -> bool:
    print(f"{CLEAR_LINE}{CR}", end="")

    if process.return_code() != 0:
        print_command_status(process, passed=False, debug=debug)
        print_command_output(process)
        return False
    else:
        print_command_status(process, passed=True, debug=debug)
        print_command_output(process)
        return True


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
            print(f"{RED_BOLD}A command failed!{NC}")
        else:
            print(f"{RED_BOLD}Error: {message}{NC}")
        exit_code = 1
    else:
        print(f"{GREEN_BOLD}Success!{NC}")

    if parsed_args.debug:
        elapsed = time.perf_counter() - start
        print(f"\nTime taken : {format_time_taken(elapsed)}")

    return exit_code


def entry_point() -> None:
    sys.exit(run(*sys.argv[1:]))


if __name__ == "__main__":
    entry_point()
