import argparse
import logging
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
import subprocess

logging.basicConfig(format="%(message)s")
logger = logging.getLogger("pyallel")


class Arguments:
    commands: list[str]
    lint_only: bool
    fail_fast: bool
    verbose: bool


def run_command(command: str) -> bytes:
    logger.info(f"Running command [{command}]")
    process = subprocess.run(
        command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    return process.stdout


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("pyallel")
    parser.add_argument("commands", help="list of commands to run", nargs="+")
    parser.add_argument(
        "-l",
        "--lint-only",
        help="only lint the code without modifying any files",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-f",
        "--fail-fast",
        help="exit immediately when a linter fails",
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


def run_commands(commands: list[str]) -> None:
    futures: dict[Future[bytes], str] = {}

    with ThreadPoolExecutor() as executor:
        for command in commands:
            futures[executor.submit(run_command, command)] = command

    for future in as_completed(futures):
        command = futures[future]
        logger.info(
            "\n".join("    " + line for line in future.result().decode().splitlines())
        )


def run() -> None:
    parser = create_parser()
    args = parser.parse_args(namespace=Arguments())

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.debug(f"CLI arguments : {args}")

    run_commands(args.commands)
