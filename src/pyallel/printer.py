from __future__ import annotations

import time

from pyallel import constants
from pyallel.colours import Colours
from pyallel.process import ProcessOutput
from pyallel.process_group import ProcessGroupOutput


class Printer:
    def __init__(self, colours: Colours | None = None, timer: bool = False) -> None:
        self._colours = colours or Colours()
        self._timer = timer
        self._prefix = f"{self._colours.dim_on}=>{self._colours.dim_off} "
        self._icon = 0
        self._printed: list[tuple[bool, str, str]] = []

    def write(
        self,
        line: str,
        include_prefix: bool = False,
        end: str = "\n",
        flush: bool = False,
        truncate: bool = False,
    ) -> None:
        truncate_num = 0
        prefix = self._prefix if include_prefix else ""
        if prefix:
            truncate_num = 6
        if truncate:
            columns = constants.COLUMNS() - truncate_num
            if get_num_lines(line, columns) > 1:
                line = truncate_line(line, columns)
        print(f"{prefix}{line}", end=end, flush=flush)

    def info(self, msg: str) -> None:
        self.write(
            f"{self._colours.white_bold}{msg}{self._colours.reset_colour}",
            include_prefix=False,
        )

    def ok(self, msg: str) -> None:
        self.write(
            f"{self._colours.green_bold}{msg}{self._colours.reset_colour}",
            include_prefix=False,
        )

    def warn(self, msg: str) -> None:
        self.write(
            f"{self._colours.yellow_bold}{msg}{self._colours.reset_colour}",
            include_prefix=False,
        )

    def error(self, msg: str) -> None:
        self.write(
            f"{self._colours.red_bold}{msg}{self._colours.reset_colour}",
            include_prefix=False,
        )

    def generate_process_output(
        self,
        output: ProcessOutput,
        tail_output: bool = False,
        include_cmd: bool = True,
        include_output: bool = True,
        include_progress: bool = True,
        include_timer: bool | None = None,
        append_newlines: bool = False,
    ) -> list[tuple[bool, str, str]]:
        out: list[tuple[bool, str, str]] = []
        line_parts: tuple[bool, str, str]

        if tail_output and output.process.lines == 0:
            return out

        if include_cmd:
            status = self.generate_process_output_status(
                output, include_progress, include_timer
            )
            line_parts = (False, status, "\n")
            out.append(line_parts)
            self._printed.append(line_parts)

        if include_output:
            lines = output.data.splitlines(keepends=True)

            if tail_output:
                output_lines = output.process.lines - 1
                if output_lines == 0:
                    lines = []
                else:
                    lines = lines[-output_lines:]

            for line in lines:
                prefix = True
                end = line[-1]
                if append_newlines and end != "\n":
                    end = "\n"
                else:
                    line = line[:-1]

                try:
                    prev_line = self._printed[-1]
                except IndexError:
                    pass
                else:
                    if prev_line[2] != "\n":
                        prefix = False

                line_parts = (prefix, line, end)
                out.append(line_parts)
                self._printed.append(line_parts)

        return out

    def generate_process_output_status(
        self,
        output: ProcessOutput,
        include_progress: bool = True,
        include_timer: bool | None = None,
    ) -> str:
        include_timer = include_timer if include_timer is not None else self._timer

        passed = None
        icon = ""
        poll = output.process.poll()
        if include_progress:
            icon = constants.ICONS[self._icon]
            if poll is not None:
                passed = poll == 0

        if passed is True:
            colour = self._colours.green_bold
            msg = "done"
            icon = constants.TICK
        elif passed is False:
            colour = self._colours.red_bold
            msg = "failed"
            icon = constants.X
        else:
            colour = self._colours.white_bold
            msg = "running"

            if not icon:
                msg += "..."

        timer = ""
        if include_timer:
            end = output.process.end
            if not output.process.end:
                end = time.perf_counter()
            elapsed = end - output.process.start
            timer = f"({format_time_taken(elapsed)})"

        command = output.process.command
        if get_num_lines(output.process.command) > 1:
            columns = constants.COLUMNS() - (len(msg) + len(timer) + 9)
            command = truncate_line(command, columns)

        out = f"{self._colours.white_bold}[{self._colours.reset_colour}{self._colours.blue_bold}{command}{self._colours.reset_colour}{self._colours.white_bold}]{self._colours.reset_colour}{colour} {msg} {icon}{self._colours.reset_colour}"

        if timer:
            out += f" {self._colours.dim_on}{timer}{self._colours.dim_off}"

        return out

    def generate_process_group_output(
        self,
        output: ProcessGroupOutput,
        interrupt_count: int = 0,
        tail_output: bool = True,
    ) -> list[tuple[bool, str, str]]:
        set_process_lines(output, interrupt_count)

        for out in output.processes:
            self.generate_process_output(out, tail_output, append_newlines=True)

        if interrupt_count == 1:
            self._printed.append((False, "", "\n"))
            self._printed.append(
                (
                    False,
                    f"{self._colours.yellow_bold}Interrupt!{self._colours.reset_colour}",
                    "\n",
                )
            )
        elif interrupt_count == 2:
            self._printed.append((False, "", "\n"))
            self._printed.append(
                (
                    False,
                    f"{self._colours.red_bold}Abort!{self._colours.reset_colour}",
                    "\n",
                )
            )

        self._icon += 1
        if self._icon == len(constants.ICONS):
            self._icon = 0

        return self._printed

    def print_process_output(
        self,
        output: ProcessOutput,
        tail_output: bool = False,
        include_cmd: bool = True,
        include_output: bool = True,
        include_progress: bool = True,
        include_timer: bool | None = None,
    ) -> None:
        for include_prefix, line, end in self.generate_process_output(
            output,
            tail_output,
            include_cmd,
            include_output,
            include_progress,
            include_timer,
        ):
            self.write(line, include_prefix, end)

        # Force a flush otherwise lines that don't end in a newline character will not get printed as they are read
        self.write("", include_prefix=False, end="", flush=True)

    def print_progress_group_output(
        self,
        output: ProcessGroupOutput,
        interrupt_count: int = 0,
        tail_output: bool = True,
    ) -> None:
        for include_prefix, line, end in self.generate_process_group_output(
            output, interrupt_count, tail_output
        ):
            self.write(line, include_prefix, end, truncate=tail_output)

    def clear_printed_lines(self) -> None:
        # Clear all the lines that were just printed
        for _, _, end in self._printed:
            if end == "\n":
                self.write(
                    f"{constants.CLEAR_LINE}{constants.UP_LINE}{constants.CLEAR_LINE}",
                    end="",
                )

        self.clear()

    def clear(self) -> None:
        self._printed.clear()


def set_process_lines(
    output: ProcessGroupOutput,
    interrupt_count: int = 0,
    lines: int = 0,
) -> None:
    lines = lines or constants.LINES() - 1
    if interrupt_count:
        lines -= 2

    # Allocate lines to processes that have a fixed percentage of lines set
    used_lines = 0
    other_processes: list[ProcessOutput] = []
    for out in output.processes:
        if not out.process.percentage_lines:
            other_processes.append(out)
            continue

        out.process.lines = int(lines * out.process.percentage_lines)
        used_lines += out.process.lines

    lines -= used_lines

    # Allocate the rest of the available lines to the other processes that don't have fixed lines set
    num_dynamic_processes = len(other_processes)
    if num_dynamic_processes:
        remainder = lines % num_dynamic_processes
        tail = lines // num_dynamic_processes

        for out in other_processes:
            out.process.lines = tail

        # If we have lines left to allocate, we give all of them to the last process
        if remainder:
            for out in other_processes[-1::-1]:
                out.process.lines += remainder
                break


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
