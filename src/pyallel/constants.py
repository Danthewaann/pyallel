import sys

IN_TTY = sys.__stdin__.isatty()

if IN_TTY:
    WHITE_BOLD = "\033[1m"
    GREEN_BOLD = "\033[1;32m"
    BLUE_BOLD = "\033[1;34m"
    RED_BOLD = "\033[1;31m"
    CLEAR_LINE = "\033[2K"
    CLEAR_SCREEN = "\033[2J"
    SAVE_CURSOR = "\033[s"
    RESTORE_CURSOR = "\033[u"
    UP_LINE = "\033[1F"
    NC = "\033[0m"
    CR = "\r"
else:
    WHITE_BOLD = ""
    GREEN_BOLD = ""
    BLUE_BOLD = ""
    RED_BOLD = ""
    CLEAR_LINE = ""
    CLEAR_SCREEN = ""
    SAVE_CURSOR = ""
    RESTORE_CURSOR = ""
    UP_LINE = ""
    NC = ""
    CR = ""


ICONS = ("/", "-", "\\", "|")
# Unicode character bytes to render different symbols in the terminal
TICK = "\u2713"
X = "\u2717"
