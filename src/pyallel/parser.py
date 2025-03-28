from __future__ import annotations

from argparse import ArgumentParser, RawTextHelpFormatter
from typing import Literal


class Arguments:
    colour: Literal["yes", "no", "auto"]
    commands: list[str]
    interactive: bool
    timer: bool
    version: bool

    def __repr__(self) -> str:
        msg = "Arguments:\n"
        padding = len(sorted(self.__dict__.keys(), key=len, reverse=True)[0]) + 1
        for field, value in self.__dict__.items():
            msg += f"    {field: <{padding}}: {value}\n"
        return msg


DESCRIPTION = r"""run and handle the output of multiple executables in %(prog)s (as in parallel)

RUNNING COMMANDS
================
to run multiple commands you must separate them using the command separator symbol (::)
    
  %(prog)s mypy . :: black .

if you want to provide options to a command you need to use the double dash symbol (--) to indicate that 
any options provided after this symbol should not be interpreted by %(prog)s 

  %(prog)s -n -- mypy -V :: black --version

commands can also be grouped using the group separator symbol (:::)

  %(prog)s echo boil kettle :: sleep 1 ::: echo make coffee

the above will print 'boil kettle' and sleep for 1 second first before printing 'make coffee'.
command groups are ran in the sequence you provide them, and if a command within a command group fails,
the rest of the command groups in the sequence are not run


modifiers can also be set for commands to augment their behaviour using the command modifier symbol (::::)

lines (only used in interactive mode):
  the lines modifier allows you to specify how many lines the command output can take up on the screen
        
    %(prog)s lines=90 :::: echo running long command... :: echo running other command...

  90 is expressed as a percentage value, which must be between 1 and 100 inclusive

SHELL SYNTAX
============
each command is executed inside its own shell, this means shell syntax is supported.
it is important to note that certain shell syntax must be escaped using backslashes (\)
or wrapped in single quotes (''), otherwise it will be evaluated in your current 
shell immediately instead of the shell that your command will run within.

some examples of using shell syntax are below (single quotes are used only if required)

  %(prog)s MYPY_FORCE_COLOR=1 mypy .            <- provide environment variables
  %(prog)s 'mypy . | tee -a mypy.log'           <- use pipes to redirect output
  %(prog)s 'cat > test.log <<< hello!'          <- use input and output redirection
  %(prog)s 'mypy .; pytest .'                   <- run commands one at a time in sequence
  %(prog)s 'echo $SHELL; $(echo mypy .)'        <- expand variables and commands to evaluate
  %(prog)s 'pytest . && mypy . || echo failed!' <- use AND (&&) and OR (||) to run commands conditionally
"""


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="pyallel",
        description=DESCRIPTION,
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        "commands",
        help="list of commands and their arguments to run in parallel",
        nargs="*",
    )
    parser.add_argument(
        "-t",
        "--no-timer",
        dest="timer",
        help="don't time how long each command is taking",
        action="store_false",
        default=True,
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
        "-V",
        "--version",
        help="print version and exit",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--colour",
        help='colour terminal output, defaults to "%(default)s"',
        choices=("yes", "no", "auto"),
        default="auto",
    )

    return parser
