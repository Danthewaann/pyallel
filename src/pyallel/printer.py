from dataclasses import dataclass, field
import sys
import time
from typing import Any

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
    return "".join(escaped_line[: columns - 3]) + "..."


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
    last_output: list[tuple[str, str]] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.prefix = ""

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

    def stderr(self, msg: Any) -> None:
        print(msg, flush=True, file=sys.stderr)

    def write(
        self, msg: str, prefix: str | None = None, end: str = "\n", flush: bool = False
    ) -> None:
        print(f"{self.prefix if prefix is None else prefix}{msg}", end=end, flush=flush)

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
            self._get_command_status(process, icon=icon, passed=passed, timer=timer),
            prefix=self.prefix,
        )

    def write_output(self, output: ProcessOutput) -> None:
        if output.data:
            lines = output.data.splitlines(keepends=True)

            if (
                output.process.id in self.output_data
                and self.output_data[output.process.id][-1] != "\n"
            ):
                self.write(
                    lines.pop(0),
                    prefix=f"{self.colours.dim_on}=>{self.colours.dim_off} ",
                    end="",
                )

            for line in lines:
                self.write(
                    line,
                    prefix=f"{self.colours.dim_on}=>{self.colours.dim_off} ",
                    end="",
                )

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

            self.last_output.append(("", status))
            if tail:
                status_num = get_num_lines(status)
                p_lines = process_lines[process_num] - status_num
                data = output.data.splitlines()[-p_lines:]
            else:
                data = output.data.splitlines()

            for line in data:
                self.last_output.append(
                    (f"{self.colours.dim_on}=>{self.colours.dim_off} ", line)
                )

            process_num += 1

        self.icon += 1
        if self.icon == len(constants.ICONS):
            self.icon = 0

        for line in self.last_output:
            if tail and get_num_lines(line[1], columns=constants.COLUMNS() - 3) > 1:
                self.write(
                    truncate_line(line[1], columns=constants.COLUMNS() - 3),
                    prefix=line[0],
                )
            else:
                self.write(line[1], prefix=line[0])

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

        output = f"{self.colours.white_bold}[{self.colours.reset_colour}{self.colours.blue_bold}{process.command}{self.colours.reset_colour}{self.colours.white_bold}]{self.colours.reset_colour}{colour} {msg} {icon}{self.colours.reset_colour}"

        if timer:
            end = process.end
            if not process.end:
                end = time.perf_counter()
            elapsed = end - process.start
            output += f" {self.colours.dim_on}({format_time_taken(elapsed)}){self.colours.dim_off}"

        return output
