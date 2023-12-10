import argparse
import logging
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
class Command:
    name: str
    process: subprocess.Popen[bytes]


def run_command(command: str) -> Command:
    process = subprocess.Popen(
        command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    return Command(name=command.split()[0], process=process)


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


def run_commands(commands: list[str]) -> dict[str, Command]:
    futures: dict[str, Command] = {}

    for command in commands:
        futures[command] = run_command(command)

    return futures


def indent(output: str) -> str:
    return "\n".join("    " + line for line in output.splitlines())


def main_loop(commands: list[str], fail_fast: bool = False) -> bool:
    futures = run_commands(commands)
    completed_futures: dict[str, Command] = {}
    passed = True

    while True:
        for icon in ICONS:
            logger.info(f"{CLEAR_LINE}\r{WHITE_BOLD}Running commands{NC} {icon}")
            time.sleep(0.1)

        for command, future in futures.items():
            if command in completed_futures:
                continue

            logger.info(f"${CLEAR_LINE}\r")

            if future.process.poll() is None:
                continue

            completed_futures[command] = future
            if future.process.returncode != 0:
                passed = False
                logger.info(f"{RED_BOLD}{future.name} : fail {X}{NC}\n")
                if future.process.stdout:
                    output = future.process.stdout.read()
                    if output:
                        logger.info(f"{indent(output.decode())}\n")

                if fail_fast:
                    return False
            else:
                logger.info(f"{GREEN_BOLD}{future.name} " f": pass {TICK}{NC}\n")
                if future.process.stdout:
                    output = future.process.stdout.read()
                    if output:
                        logger.debug(f"{indent(output.decode())}\n")

        if len(completed_futures) == len(futures):
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
