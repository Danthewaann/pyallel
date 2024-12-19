from dataclasses import dataclass, field
import time

from pyallel import constants
from pyallel.colours import Colours
from pyallel.process import Process, ProcessOutput
from pyallel.process_group import ProcessGroupOutput


def get_num_lines(line: str, columns: int | None = None) -> int:
    lines = 0
    columns = columns or constants.COLUMNS()
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


def truncate_line(line: str, columns: int | None = None) -> str:
    columns = columns or constants.COLUMNS()
    escaped_line = constants.ANSI_ESCAPE.sub("", line)
    return "".join(escaped_line[:columns]) + "..."


def format_time_taken(time_taken: float) -> str:
    time_taken = round(time_taken, 1)
    seconds = time_taken % (24 * 3600)

    return f"{seconds}s"


@dataclass
class Printer:
    colours: Colours = field(default_factory=Colours)
    timer: bool = False
    debug: bool = False
    prefix: str = field(init=False)
    icon: int = field(init=False, default=0)
    output_data: dict[int, str] = field(init=False, default_factory=dict)
    last_output: list[tuple[bool, str]] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.prefix = f"{self.colours.dim_on}=>{self.colours.dim_off} "

    def info(self, msg: str) -> None:
        print(
            f"{self.colours.white_bold}{msg}{self.colours.reset_colour}",
            flush=True,
        )

    def ok(self, msg: str) -> None:
        print(
            f"{self.colours.green_bold}{msg}{self.colours.reset_colour}",
            flush=True,
        )

    def warn(self, msg: str) -> None:
        print(
            f"{self.colours.yellow_bold}{msg}{self.colours.reset_colour}",
            flush=True,
        )

    def error(self, msg: str, flush: bool = False) -> None:
        print(
            f"{self.colours.red_bold}{msg}{self.colours.reset_colour}",
            flush=flush,
        )

    def write(
        self, msg: str, prefix: bool = False, end: str = "\n", flush: bool = False
    ) -> None:
        print(f"{self.prefix if prefix else ''}{msg}", end=end, flush=flush)

    def write_command_status(
        self,
        process: Process,
        icon: str | None = None,
        passed: bool | None = None,
        timer: bool | None = None,
    ) -> None:
        if timer is None:
            timer = self.timer

        self.write(
            self._get_command_status(process, icon=icon, passed=passed, timer=timer)
        )

    def write_output(self, output: ProcessOutput) -> None:
        if output.data:
            lines = output.data.splitlines(keepends=True)

            if (
                output.process.id in self.output_data
                and self.output_data[output.process.id][-1] != "\n"
            ):
                self.write(lines.pop(0), end="")

            for line in lines:
                self.write(line, prefix=True, end="")

            self.output_data[output.process.id] = output.data

    def interactive_print(self, outputs: ProcessGroupOutput, tail: bool = True) -> None:
        process_num = 0
        process_lines = self.get_process_lines(outputs)

        for output in outputs.processes:
            if output.process.poll() is not None:
                status = self._get_command_status(
                    output.process,
                    passed=output.process.return_code() == 0,
                    timer=self.timer,
                )
            else:
                status = self._get_command_status(
                    output.process,
                    icon=constants.ICONS[self.icon],
                    timer=self.timer,
                )

            self.last_output.append((False, status))
            data = output.data.splitlines()
            if tail:
                status_num = get_num_lines(status)
                p_lines = process_lines[process_num] - status_num
                data = data[-p_lines:]

            for line in data:
                self.last_output.append((True, line))

            process_num += 1

        self.icon += 1
        if self.icon == len(constants.ICONS):
            self.icon = 0

        for prefix, line in self.last_output:
            columns = constants.COLUMNS() - len(self.prefix if prefix else "")
            if tail and get_num_lines(line, columns) > 1:
                line = truncate_line(line, columns)
            self.write(line, prefix=prefix)

    def get_process_lines(
        self, outputs: ProcessGroupOutput, lines: int | None = None
    ) -> list[int]:
        num_processes = len(outputs.processes)
        process_lines: list[int] = [0 for _ in range(num_processes)]

        lines = lines or constants.LINES() - 1

        remainder = lines % num_processes
        tail = lines // num_processes

        for i in range(num_processes):
            process_lines[i] = tail

        if remainder:
            process_lines[-1] += remainder

        return process_lines

    def clear(self) -> None:
        # Clear all the lines that were just printed
        for _ in range(len(self.last_output)):
            self.clear_line()

        self.last_output.clear()

    def clear_line(self) -> None:
        print(
            f"{constants.CLEAR_LINE}{constants.UP_LINE}{constants.CLEAR_LINE}", end=""
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

        output = f"{self.colours.white_bold}[{self.colours.reset_colour}{self.colours.blue_bold}{process.command}{self.colours.reset_colour}{self.colours.white_bold}]{self.colours.reset_colour}{colour} {msg} {icon}{self.colours.reset_colour}"

        if timer:
            end = process.end
            if not process.end:
                end = time.perf_counter()
            elapsed = end - process.start
            output += f" {self.colours.dim_on}({format_time_taken(elapsed)}){self.colours.dim_off}"

        return output
