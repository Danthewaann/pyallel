import argparse
import logging
import os
import sys
import time
from datetime import timedelta
from dataclasses import dataclass
import importlib.metadata
import subprocess

logging.basicConfig(format="%(message)s")
logging.StreamHandler.terminator = ""
logger = logging.getLogger("pyallel")

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
    verbose: bool
    version: bool


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
        "-V",
        "--verbose",
        help="print all output for provided commands",
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


def main_loop(commands: list[str], fail_fast: bool = False) -> bool:
    processes = run_commands(commands)
    completed_processes: set[str] = set()
    passed = True

    while True:
        for icon in ICONS:
            logger.info(f"{CLEAR_LINE}\r{WHITE_BOLD}Running commands{NC} {icon}")
            time.sleep(0.1)

        for process in processes:
            if process.name in completed_processes:
                continue

            if process.process.poll() is None:
                continue

            logger.info(f"${CLEAR_LINE}\r")
            elapsed = time.perf_counter() - process.start
            completed_processes.add(process.name)
            if process.process.returncode != 0:
                passed = False
                logger.info(f"{RED_BOLD}{process.name} ")
                logger.debug(f"[{timedelta(seconds=elapsed)}] ")
                logger.info(f": fail {X}{NC}\n")
                if process.process.stdout:
                    output = process.process.stdout.read()
                    if output:
                        logger.info(f"{indent(output.decode())}\n")

                if fail_fast:
                    return False
            else:
                logger.info(f"{GREEN_BOLD}{process.name} ")
                logger.debug(f"[{timedelta(seconds=elapsed)}] ")
                logger.info(f": pass {TICK}{NC}\n")
                if process.process.stdout:
                    output = process.process.stdout.read()
                    if output:
                        logger.debug(f"{indent(output.decode())}\n")

        if len(completed_processes) == len(processes):
            break

    return passed


def run() -> None:
    parser = create_parser()
    args = parser.parse_args(namespace=Arguments())

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if args.version:
        my_version = importlib.metadata.version("pyallel")
        logger.info("%s\n", my_version)
        sys.exit(0)

    start_time = time.perf_counter()

    if not main_loop(args.commands, args.fail_fast):
        logger.info(f"\n{RED_BOLD}A command failed!{NC}\n")
    else:
        logger.info(f"\n{GREEN_BOLD}Success!{NC}\n")

    elapsed_time = time.perf_counter() - start_time
    logger.debug(f"Time taken : {timedelta(seconds=elapsed_time)}\n")
