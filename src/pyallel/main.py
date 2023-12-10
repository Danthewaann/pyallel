import argparse
import os
import sys
import time
from datetime import timedelta
from dataclasses import dataclass
import importlib.metadata
import subprocess

WHITE_BOLD = "\033[1m"
GREEN_BOLD = "\033[1;32m"
RED_BOLD = "\033[1;31m"
NC = "\033[0m"
CLEAR_LINE = "\033[2K"
UP_LINE = "\033[1F"
ICONS = ("/", "-", "\\", "|")

# Unicode character bytes to render different symbols in the terminal
TICK = "\u2713"
X = "\u2717"


class Arguments:
    commands: list[str]
    fail_fast: bool
    interactive: bool
    debug: bool
    verbose: bool
    version: bool

    def __repr__(self) -> str:
        msg = "Arguments:\n"
        padding = len(sorted(self.__dict__.keys(), key=len, reverse=True)[0]) + 1
        for field, value in self.__dict__.items():
            msg += f"    {field: <{padding}}: {value}\n"
        return msg


@dataclass
class Process:
    name: str
    args: list[str]
    start: float
    process: subprocess.Popen[bytes]


def run_command(command: str) -> Process:
    executable, *args = command.split()
    env = os.environ.copy()
    start = time.perf_counter()
    process = subprocess.Popen(
        [executable, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        # TODO: need to provide a way to supply environment variables
        # for each provided command
        env=env | {"MYPY_FORCE_COLOR": "1"},
    )
    return Process(name=executable, args=args, start=start, process=process)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("pyallel")
    parser.add_argument("commands", help="list of commands to run", nargs="+")
    parser.add_argument(
        "-f",
        "--fail-fast",
        help="exit immediately when a command fails",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-n",
        "--non-interactive",
        help="run in non-interactive mode",
        action="store_false",
        dest="interactive",
        default=True,
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="output debug info for each command",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-V",
        "--verbose",
        help="run in verbose mode",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-v",
        "--version",
        help="print version and exit",
        action="store_true",
        default=False,
    )

    return parser


def run_commands(commands: list[str]) -> list[Process]:
    return [run_command(command) for command in commands]


def indent(output: str) -> str:
    return "\n".join("    " + line for line in output.splitlines())


def format_time_taken(time_taken: float) -> str:
    return str(timedelta(seconds=time_taken))


def print_command_status(process: Process, passed: bool, debug: bool = False) -> None:
    colour = RED_BOLD
    msg = "failed"
    icon = X
    if passed:
        colour = GREEN_BOLD
        msg = "done"
        icon = TICK

    print(f"[{colour}{process.name}", end="")

    if debug:
        print(f" {' '.join(process.args)}", end="")

    print(f"{NC}]{colour} {msg} ", end="")

    if debug:
        elapsed = time.perf_counter() - process.start
        print(f"in {format_time_taken(elapsed)} ", end="")

    print(f"{icon}{NC}")


def print_command_output(process: Process) -> None:
    if process.process.stdout:
        output = process.process.stdout.read()
        if output:
            print(f"{indent(output.decode())}")
    print()


def main_loop(
    commands: list[str],
    fail_fast: bool = False,
    interactive: bool = False,
    debug: bool = False,
) -> bool:
    processes = run_commands(commands)
    completed_processes: set[str] = set()
    passed = True

    if not interactive:
        print(f"{WHITE_BOLD}Running commands...{NC}\n")

    while True:
        if interactive:
            for icon in ICONS:
                print(f"{CLEAR_LINE}\r{WHITE_BOLD}Running commands{NC} {icon}", end="")
                time.sleep(0.1)

        for process in processes:
            if process.name in completed_processes or process.process.poll() is None:
                continue

            print(f"${CLEAR_LINE}\r", end="")
            completed_processes.add(process.name)

            if process.process.returncode != 0:
                print_command_status(process, passed=False, debug=debug)
                print_command_output(process)
                passed = False

                if fail_fast:
                    return False
            else:
                print_command_status(process, passed=True, debug=debug)
                print_command_output(process)

        if len(completed_processes) == len(processes):
            break

    return passed


def run() -> None:
    parser = create_parser()
    args = parser.parse_args(namespace=Arguments())
    if args.version:
        my_version = importlib.metadata.version("pyallel")
        print(my_version)
        sys.exit(0)

    if args.verbose:
        print(args)

    start_time = time.perf_counter()

    exit_code = 0
    status = main_loop(args.commands, args.fail_fast, args.interactive, args.debug)
    if not status:
        print(f"{RED_BOLD}A command failed!{NC}")
        exit_code = 1
    else:
        print(f"{GREEN_BOLD}Success!{NC}")

    elapsed_time = time.perf_counter() - start_time
    if args.verbose:
        print(f"\nTime taken : {format_time_taken(elapsed_time)}")
    sys.exit(exit_code)
