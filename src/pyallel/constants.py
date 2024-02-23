import os
import sys

IN_TTY = sys.stdout.isatty()


if IN_TTY:
    def COLUMNS() -> int:
        return os.get_terminal_size().columns

    def LINES() -> int:
        return os.get_terminal_size().lines

else:
    def COLUMNS() -> int:
        return sys.maxsize

    def LINES() -> int:
        return sys.maxsize


ICONS = ("/", "-", "\\", "|")
# Unicode character bytes to render different symbols in the terminal
TICK = "\u2713"
X = "\u2717"
