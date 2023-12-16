from __future__ import annotations

from argparse import ArgumentParser, RawTextHelpFormatter


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


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="pyallel",
        description="Run and handle the output of multiple executables in pyallel (as in parallel)",
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        "commands",
        help='list of quoted commands to run e.g "mypy ." "black ."\n\n'
        "can provide environment variables to each command like so:\n\n"
        '     "MYPY_FORCE_COLOR=1 mypy ."',
        nargs="*",
    )
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
