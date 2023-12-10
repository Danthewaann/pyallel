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
    time_taken: float


def run_command(command: str) -> Command:
    start = time.perf_counter()
    process = subprocess.run(
        command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    end = time.perf_counter()
    return Command(
        name=command.split()[0],
        exit_code=process.returncode,
        output=process.stdout,
        time_taken=end - start,
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


def main_loop(commands: list[str]) -> bool:
    futures = run_commands(commands)
    completed_futures: dict[Future[Command], str] = {}
    passed = True

    while True:
        for icon in ICONS:
            logger.info(f"{CLEAR_LINE}\r{WHITE_BOLD}Running commands{NC} {icon}")
            time.sleep(0.1)

        for future in as_completed(futures):
            if future in completed_futures:
                continue

            logger.info(f"${CLEAR_LINE}\r")

            completed_futures[future] = futures[future]
            command = future.result()
            if command.exit_code != 0:
                passed = False
                logger.info(
                    f"{RED_BOLD}{command.name} "
                    f"[{timedelta(seconds=command.time_taken)}] "
                    f": fail {X}{NC}\n"
                    f"{indent(command.output.decode())}\n"
                )
            else:
                logger.info(
                    f"{GREEN_BOLD}{command.name} "
                    f"[{timedelta(seconds=command.time_taken)}] "
                    f": pass {TICK}{NC}\n"
                )
                if command.output:
                    logger.debug(f"{indent(command.output.decode())}\n")

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

    start_time = time.perf_counter()

    if not main_loop(args.commands):
        logger.info(f"\n{RED_BOLD}A command failed!{NC}\n")
    else:
        logger.info(f"\n{GREEN_BOLD}Success!{NC}\n")

    elapsed_time = time.perf_counter() - start_time
    logger.debug(f"Time taken : {timedelta(seconds=elapsed_time)}\n")
