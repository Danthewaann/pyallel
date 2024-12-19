import time

from pyallel import constants
from pyallel.colours import Colours
from pyallel.process import Process, ProcessOutput
from pyallel.process_group import ProcessGroupOutput


class Printer:
    def __init__(self, colours: Colours | None = None, timer: bool = False) -> None:
        self.colours = colours or Colours()
        self.timer = timer
        self.prefix = f"{self.colours.dim_on}=>{self.colours.dim_off} "
        self.icon = 0
        self.output_data: dict[int, str] = {}
        self.last_output: list[tuple[bool, str, str]] = []

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

    def generate_process_output(
        self,
        output: ProcessOutput,
        tail: bool = False,
        include_cmd: bool = True,
        include_output: bool = True,
        include_progress: bool = True,
        include_timer: bool = True,
    ) -> list[tuple[bool, str, str]]:
        out: list[tuple[bool, str, str]] = []

        if include_cmd:
            if output.process.poll() is not None:
                status = self._get_command_status(
                    output.process,
                    passed=output.process.return_code() == 0
                    if include_progress
                    else None,
                    timer=include_timer,
                )
            else:
                status = self._get_command_status(
                    output.process,
                    icon=constants.ICONS[self.icon] if include_progress else None,
                    timer=include_timer,
                )
            out.append((False, status, "\n"))
            self.last_output.append((False, status, "\n"))

        if include_output:
            data = output.data.splitlines(keepends=True)

            if tail:
                status_num = get_num_lines(status)
                p_lines = output.lines - status_num
                data = data[-p_lines:]

            for line in data:
                end = line[-1]
                if end != "\n":
                    end = ""
                else:
                    line = line[:-1]

                try:
                    prev_line = self.last_output[-1]
                except IndexError:
                    prefix = True
                else:
                    if prev_line[2] != "\n":
                        prefix = False
                    else:
                        prefix = True

                out.append((prefix, line, end))
                self.last_output.append((prefix, line, end))

        return out

    def print_process_output(
        self,
        output: ProcessOutput,
        tail: bool = False,
        include_cmd: bool = True,
        include_output: bool = True,
        include_progress: bool = True,
        include_timer: bool = True,
    ) -> None:
        out = self.generate_process_output(
            output, tail, include_cmd, include_output, include_progress, include_timer
        )

        for prefix, line, end in out:
            self.print_line(prefix, line, end)

    def generate_process_group_output(
        self, pg_output: ProcessGroupOutput, interrupt_count: int = 0, tail: bool = True
    ) -> list[tuple[bool, str, str]]:
        process_num = 0
        process_lines = self.get_process_lines(pg_output, interrupt_count)

        for output in pg_output.processes:
            output.lines = process_lines[process_num]
            self.generate_process_output(output, tail)
            process_num += 1

        if interrupt_count == 1:
            self.last_output.append((False, "", "\n"))
            self.last_output.append(
                (
                    False,
                    f"{self.colours.yellow_bold}Interrupt!{self.colours.reset_colour}",
                    "\n",
                )
            )
        elif interrupt_count == 2:
            self.last_output.append((False, "", "\n"))
            self.last_output.append(
                (
                    False,
                    f"{self.colours.red_bold}Abort!{self.colours.reset_colour}",
                    "\n",
                )
            )

        self.icon += 1
        if self.icon == len(constants.ICONS):
            self.icon = 0

        return self.last_output

    def print_progress_group_output(
        self, output: ProcessGroupOutput, interrupt_count: int = 0, tail: bool = True
    ) -> None:
        out = self.generate_process_group_output(output, interrupt_count, tail)

        for prefix, line, end in out:
            self.print_line(prefix, line, end, tail)

    def print_line(
        self, prefix: bool, line: str, end: str = "\n", tail: bool = False
    ) -> None:
        if tail:
            columns = constants.COLUMNS() - len(self.prefix if prefix else "")
            if get_num_lines(line, columns) > 1:
                line = truncate_line(line, columns)
        self.write(line, prefix=prefix, end=end)

    def get_process_lines(
        self,
        outputs: ProcessGroupOutput,
        interrupt_count: int = 0,
        lines: int | None = None,
    ) -> list[int]:
        num_processes = len(outputs.processes)
        process_lines: list[int] = [0 for _ in range(num_processes)]

        lines = lines or constants.LINES() - 1

        if interrupt_count:
            lines -= 2

        remainder = lines % num_processes
        tail = lines // num_processes

        for i in range(num_processes):
            process_lines[i] = tail

        if remainder:
            process_lines[-1] += remainder

        return process_lines

    def clear(self) -> None:
        # Clear all the lines that were just printed
        for _, _, end in self.last_output:
            if end == "\n":
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
