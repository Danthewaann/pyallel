import re
import shutil
import sys

IN_TTY = sys.stdout.isatty()

# From: https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
CLEAR_LINE = "\033[2K"
UP_LINE = "\033[1A\r"
DOWN_LINE = "\033[1B\r"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
# Terminal synchronized update mode: https://gist.github.com/christianparpart/d8a62cc1ab659194337d73e399004036
# Terminals that don't recognise this just ignore it, so it's safe to always emit
SYNC_UPDATE_BEGIN = "\033[?2026h"
SYNC_UPDATE_END = "\033[?2026l"
ANSI_ESCAPE = re.compile(r"(\x9B|\x1B\[|\x1B\()[0-?]*[ -\/]*[@-~]")

if IN_TTY:

    def columns() -> int:
        return shutil.get_terminal_size().columns

    def lines() -> int:
        return shutil.get_terminal_size().lines

else:

    def columns() -> int:
        return sys.maxsize

    def lines() -> int:
        return sys.maxsize


ICONS = ("/", "-", "\\", "|")

# Unicode character bytes to render different symbols in the terminal
TICK = "\u2714"
X = "\u2718"
