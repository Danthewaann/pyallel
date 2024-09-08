from dataclasses import dataclass, field

from pyallel import constants
from pyallel.colours import Colours
from pyallel.process_group import Output


@dataclass
class Printer:
    colours: Colours = field(default_factory=Colours)
    prefix: str = ""

    def __post_init__(self) -> None:
        self.prefix = f"{self.colours.dim_on}=>{self.colours.dim_off} "

    def info(self, msg: str) -> None:
        print(
            f"{self.prefix}{self.colours.white_bold}{msg}{self.colours.reset_colour}",
            flush=True,
        )

    def ok(self, msg: str) -> None:
        print(
            f"{self.prefix}{self.colours.green_bold}{msg}{self.colours.reset_colour}",
            flush=True,
        )

    def warn(self, msg: str) -> None:
        print(
            f"{self.prefix}{self.colours.yellow_bold}{msg}{self.colours.reset_colour}",
            flush=True,
        )

    def error(self, msg: str, flush: bool = False) -> None:
        print(
            f"{self.prefix}{self.colours.red_bold}{msg}{self.colours.reset_colour}",
            flush=flush,
        )

    def write(self, msg: str, end: str = "\n", flush: bool = False) -> None:
        print(msg, end=end, flush=flush)

    def write_outputs(self, outputs: list[Output]) -> None:
        for output in outputs:
            if output.data:
                self.write(output.data)

    def clear_line(self) -> None:
        print(
            f"{constants.CLEAR_LINE}{constants.UP_LINE}{constants.CLEAR_LINE}",
            end="",
        )
