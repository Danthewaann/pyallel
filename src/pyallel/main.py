import argparse
import logging
import time
from datetime import timedelta
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
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


@dataclass
class Command:
    name: str
    exit_code: int
    output: bytes


def run_command(command: str) -> Command:
    process = subprocess.run(
        command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    return Command(
        name=command.split()[0], exit_code=process.returncode, output=process.stdout
    )


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

    return parser


def run_commands(commands: list[str]) -> dict[Future[Command], str]:
    futures: dict[Future[Command], str] = {}

    with ThreadPoolExecutor() as executor:
        for command in commands:
            futures[executor.submit(run_command, command)] = command

    return futures


def indent(output: str) -> str:
    return "\n".join("    " + line for line in output.splitlines())


def main_loop(commands: list[str]) -> None:
    futures = run_commands(commands)
    completed_futures: dict[Future[Command], str] = {}

    while True:
        for icon in ICONS:
            logger.info(f"{CLEAR_LINE}\r{WHITE_BOLD}Running commands{NC} {icon}")
            time.sleep(0.1)

        for future in as_completed(futures):
            if future in completed_futures:
                continue

            logger.info(f"${CLEAR_LINE}\r")

            completed_futures[future] = futures[future]
            result = future.result()
            if result.exit_code != 0:
                logger.info(f"{RED_BOLD}{result.name} : fail {X}{NC}\n")
                logger.info(indent(result.output.decode()))
            else:
                logger.info(f"{GREEN_BOLD}{result.name} : pass {TICK}{NC}\n")
                if result.output:
                    logger.debug(indent(result.output.decode()))

        if len(completed_futures) == len(futures):
            break


def run() -> None:
    parser = create_parser()
    args = parser.parse_args(namespace=Arguments())

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.debug(f"CLI arguments : {args}\n")

    start_time = time.perf_counter()

    main_loop(args.commands)

    elapsed_time = time.perf_counter() - start_time
    logger.info(f"Time taken : {timedelta(seconds=elapsed_time)}\n")
