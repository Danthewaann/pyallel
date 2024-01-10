from __future__ import annotations

from argparse import ArgumentParser, RawTextHelpFormatter


class Arguments:
    commands: list[str]
    interactive: bool
    debug: bool
    verbose: bool
    version: bool
    stream: bool

    def __repr__(self) -> str:
        msg = "Arguments:\n"
        padding = len(sorted(self.__dict__.keys(), key=len, reverse=True)[0]) + 1
        for field, value in self.__dict__.items():
            msg += f"    {field: <{padding}}: {value}\n"
        return msg


COMMANDS_HELP = """list of quoted commands to run e.g "mypy ." "black ."

can provide environment variables to each command like so:

     "MYPY_FORCE_COLOR=1 mypy ."

command modes:

can also provide modes to commands to do extra things:

    "tail=10 :: pytest ." <-- only output the last 10 lines, doesn't work in --no-stream mode
"""


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="pyallel",
        description="Run and handle the output of multiple executables in pyallel (as in parallel)",
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        "commands",
        help=COMMANDS_HELP,
        nargs="*",
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="output debug info for each command",
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
        "-s",
        "--no-stream",
        help="don't stream output of each command",
        action="store_false",
        default=True,
        dest="stream",
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
