import re
import shutil
import sys

IN_TTY = sys.stdout.isatty()
CLEAR_LINE = "\033[2K"
UP_LINE = "\033[1F"
ANSI_ESCAPE = re.compile(r"(\x9B|\x1B\[|\x1B\()[0-?]*[ -\/]*[@-~]")

if IN_TTY:

    def COLUMNS() -> int:
        return shutil.get_terminal_size().columns

    def LINES() -> int:
        return shutil.get_terminal_size().lines

else:

    def COLUMNS() -> int:
        return sys.maxsize

    def LINES() -> int:
        return sys.maxsize


ICONS = ("/", "-", "\\", "|")

# Unicode character bytes to render different symbols in the terminal
TICK = "\u2714"
X = "\u2718"
