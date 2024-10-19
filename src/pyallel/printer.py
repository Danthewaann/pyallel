from dataclasses import dataclass, field
import time

from pyallel import constants
from pyallel.colours import Colours
from pyallel.process import Process
from pyallel.process_group import Output

def get_num_lines(output: str, columns: int | None = None) -> int:
    lines = 0
    columns = columns or constants.COLUMNS()
    for line in output.splitlines():
        line = constants.ANSI_ESCAPE.sub("", line)
        length = len(line)
        line_lines = 1
        if length > columns:
            line_lines = length // columns
            remainder = length % columns
            if remainder:
                line_lines += 1
        lines += 1 * line_lines
    return lines

def format_time_taken(time_taken: float) -> str:
    time_taken = round(time_taken, 1)
    seconds = time_taken % (24 * 3600)

    return f"{seconds}s"

@dataclass
class Printer:
    colours: Colours = field(default_factory=Colours)
    prefix: str = ""
    icon: int = 0
    timer: bool = False

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

    def write_outputs(self, outputs: list[list[Output]], clear: bool = True) -> None:
        all_output: list[str] = []
        for pgm_output in outputs:
            for output in pgm_output:
                if output.process.poll() is not None:
                    status = self._get_command_status(output.process, passed=output.process.return_code() == 0, timer=self.timer)
                    all_output.append(status)
                else:
                    status = self._get_command_status(output.process, icon=constants.ICONS[self.icon], timer=self.timer)
                    all_output.append(status)
                if output.data:
                    for line in output.data.splitlines():
                        all_output.append(line)

        for line in all_output:
            print(line)

        # Clear all the lines that were just printed
        if clear:
            for _ in range(len(all_output)):
                self.clear_line()

        self.icon += 1
        if self.icon == len(constants.ICONS):
            self.icon = 0


    def clear_line(self) -> None:
        print(
            f"{constants.CLEAR_LINE}{constants.UP_LINE}{constants.CLEAR_LINE}",
            end="",
        )

    def _get_command_status(
        self,
        process: Process,
        icon: str | None = None,
        passed: bool | None = None,
        timer: bool = False,
    ) -> str:
        if passed is True:
            colour = self.colours.green_bold
            msg = "done"
            icon = icon or constants.TICK
        elif passed is False:
            colour = self.colours.red_bold
            msg = "failed"
            icon = icon or constants.X
        else:
            colour = self.colours.white_bold
            msg = "running"
            icon = icon or ""
            if not icon:
                msg += "..."

        output = f"{self.colours.dim_on}=>{self.colours.dim_off} {self.colours.white_bold}[{self.colours.reset_colour}{self.colours.blue_bold}{process.command}{self.colours.reset_colour}{self.colours.white_bold}]{self.colours.reset_colour}{colour} {msg} {icon}{self.colours.reset_colour}"

        if timer:
            end = process.end
            if not process.end:
                end = time.perf_counter()
            elapsed = end - process.start
            output += f" {self.colours.dim_on}({format_time_taken(elapsed)}){self.colours.dim_off}"

        return output
