from __future__ import annotations

import time
from typing import Protocol

from pyallel import constants
from pyallel.colours import Colours
from pyallel.process import Process, ProcessOutput
from pyallel.process_group import ProcessGroupOutput
from pyallel.process_group_manager import ProcessGroupManager


class Printer(Protocol):
    def print(self, process_group_manager: ProcessGroupManager) -> None:
        """Print output obtained from the provided process group manager.

        Args:
            process_group_manager: manager to obtain output from
        """


class ConsolePrinter:
    def __init__(self, colours: Colours | None = None, timer: bool = False) -> None:
        self._colours = colours or Colours()
        self._timer = timer
        self._prefix = f"{self._colours.dim_on}=>{self._colours.dim_off} "
        self._icon = 0
        self._to_print: list[tuple[bool, str, str]] = []

    def write(
        self,
        line: str,
        include_prefix: bool = False,
        end: str = "\n",
        flush: bool = False,
        truncate: bool = False,
        columns: int | None = None,
    ) -> None:
        truncate_num = 0
        prefix = self._prefix if include_prefix else ""
        columns = columns or constants.COLUMNS()
        if prefix:
            truncate_num = 6
        if truncate:
            columns = columns - truncate_num
            if self.get_num_lines(line, columns) > 1:
                line = self.truncate_line(line, columns)
        print(f"{prefix}{line}", end=end, flush=flush)

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
            self._to_print.append(line_parts)

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
                    prev_line = self._to_print[-1]
                except IndexError:
                    pass
                else:
                    if prev_line[2] != "\n":
                        prefix = False

                line_parts = (prefix, line, end)
                out.append(line_parts)
                self._to_print.append(line_parts)

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
            timer = f"({self.format_time_taken(elapsed)})"

        command = output.process.command
        if self.get_num_lines(output.process.command) > 1:
            columns = constants.COLUMNS() - (len(msg) + len(timer) + 9)
            command = self.truncate_line(command, columns)

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
        self.set_process_lines(output, interrupt_count)

        for out in output.processes:
            self.generate_process_output(out, tail_output, append_newlines=True)

        if interrupt_count == 1:
            self._to_print.append((False, "", "\n"))
            self._to_print.append(
                (
                    False,
                    f"{self._colours.yellow_bold}Interrupt!{self._colours.reset_colour}",
                    "\n",
                )
            )
        elif interrupt_count == 2:
            self._to_print.append((False, "", "\n"))
            self._to_print.append(
                (
                    False,
                    f"{self._colours.red_bold}Abort!{self._colours.reset_colour}",
                    "\n",
                )
            )

        self._icon += 1
        if self._icon == len(constants.ICONS):
            self._icon = 0

        return self._to_print

    def set_process_lines(
        self,
        output: ProcessGroupOutput,
        interrupt_count: int = 0,
        lines: int = 0,
    ) -> None:
        lines = lines or constants.LINES() - 1
        if interrupt_count:
            lines -= 2

        # Allocate lines to processes that have a fixed percentage of lines set
        allocated_process_lines = lines // len(output.processes)
        processes_with_dynamic_lines: list[ProcessOutput] = []
        used_lines = 0
        for process_output in output.processes:
            # This process output doesn't have percentage_lines set, so skip it
            if not process_output.process.percentage_lines:
                processes_with_dynamic_lines.append(process_output)
                continue

            process_output.process.lines = int(
                lines * process_output.process.percentage_lines
            )
            used_lines += process_output.process.lines

        # Remove the used lines from the total available lines
        lines -= used_lines

        while lines:
            # Calculate how many lines each process should have based on how many processes and lines are left
            num_processes = len(processes_with_dynamic_lines) or 1
            allocated_process_lines = lines // num_processes
            processes_with_excess_output: list[ProcessOutput] = []
            recalculate_lines = False
            for process_output in processes_with_dynamic_lines:
                # If the number of lines in this process output is less than how many terminal lines we would allocate it,
                # Set it's allocated terminal lines to the exact number of lines in its output and remove this number from
                # the total available terminal lines
                if process_output.lines < allocated_process_lines:
                    process_output.process.lines = process_output.lines
                    lines -= process_output.process.lines
                    recalculate_lines = True
                    continue

                processes_with_excess_output.append(process_output)

            # We need to re-calcuate how many terminal lines we can allocate to each process if the output of at least one process
            # contains less lines than what we would normally allocate it. This is done so we can allocate these extra lines to the
            # other processes that contain more lines of output.
            if recalculate_lines:
                processes_with_dynamic_lines = processes_with_excess_output
            else:
                # All remaining processes exceed the number of terminal lines we will allocate them, so allocate them
                # their terminal lines as normal and break out of the while loop
                for process_output in processes_with_excess_output:
                    process_output.process.lines = allocated_process_lines
                    lines -= allocated_process_lines

                # If there is any lines left, allocate them to the process that currently contains the most lines in its output, or
                # allocate them to the first process if no process contains enough lines
                if lines:
                    process_with_most_lines: ProcessOutput | None = None
                    most_lines = 0
                    for process_output in output.processes:
                        if process_output.process.lines > most_lines:
                            process_with_most_lines = process_output
                            most_lines = process_output.process.lines

                    if not process_with_most_lines:
                        output.processes[0].process.lines += lines
                    else:
                        process_with_most_lines.process.lines += lines

                break

    def get_num_lines(self, line: str, columns: int | None = None) -> int:
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

    def truncate_line(self, line: str, columns: int | None = None) -> str:
        columns = columns or constants.COLUMNS()
        escaped_line = constants.ANSI_ESCAPE.sub("", line)
        return "".join(escaped_line[:columns]) + "..."

    def format_time_taken(self, time_taken: float) -> str:
        time_taken = round(time_taken, 1)
        seconds = time_taken % (24 * 3600)

        return f"{seconds}s"


class InteractiveConsolePrinter(ConsolePrinter):
    def __init__(self, colours: Colours | None = None, timer: bool = False) -> None:
        super().__init__(colours, timer)
        self._last_printed: list[tuple[bool, str, str]] = []

    def print(self, process_group_manager: ProcessGroupManager) -> None:
        output = process_group_manager.get_cur_process_group_output()
        self.print_process_group_output(output, process_group_manager._interrupt_count)

        poll = process_group_manager.poll()
        if poll is not None:
            self.clear_last_printed_lines()
            self.reset()
            self.print_process_group_output(
                output, process_group_manager._interrupt_count, tail_output=False
            )
            self.reset()

    def print_process_group_output(
        self,
        output: ProcessGroupOutput,
        interrupt_count: int = 0,
        tail_output: bool = True,
    ) -> None:
        columns = constants.COLUMNS()
        self.generate_process_group_output(output, interrupt_count, tail_output)

        num_lines_to_print = len(self._to_print)
        num_last_printed_lines = len(self._last_printed)

        # If we don't have any last printed lines or we don't want to tail the output,
        # we just print all the new lines
        if not num_last_printed_lines or not tail_output:
            for include_prefix, line, end in self._to_print:
                self.write(
                    line, include_prefix, end, truncate=tail_output, columns=columns
                )
        else:
            # Compare the number of last lines and new lines and only update what has changed.
            #
            # Move the cursor up the amount the lines that were last printed so we can start
            # comparing the last printed lines with the new lines that were generated
            print(f"\033[{num_last_printed_lines}A", end="")
            cursor_line = 0
            for cur_line, line_parts in enumerate(
                self._last_printed[:num_lines_to_print]
            ):
                # If the current line is not the same as it's newly generated version, we update the line
                if line_parts[1] != self._to_print[cur_line][1]:
                    include_prefix, line, end = self._to_print[cur_line]
                    # Jump to the line that needs to be changed
                    lines_to_jump = cur_line - cursor_line
                    if lines_to_jump:
                        print(f"\033[{lines_to_jump}B\r", end="")
                    # Clear the current line
                    print(f"{constants.CLEAR_LINE}\r", end="")
                    # Write the new line, this will move the cursor to the next line automatically
                    self.write(
                        line, include_prefix, end, truncate=tail_output, columns=columns
                    )
                    # Need to set the cursor_line to be the current line + 1 as the above write
                    # will move the cursor to the next line
                    cursor_line = cur_line + 1

            if num_lines_to_print > num_last_printed_lines:
                # Jump to the start of the new lines that needs to be printed
                lines_to_jump = num_last_printed_lines - cursor_line
                if lines_to_jump:
                    print(f"\033[{lines_to_jump}B\r", end="")

                # Just print the new lines as normal
                for line_parts in self._to_print[num_last_printed_lines:]:
                    include_prefix, line, end = line_parts
                    self.write(
                        line, include_prefix, end, truncate=tail_output, columns=columns
                    )
            else:
                # Jump to the end of the output
                lines_to_jump = num_lines_to_print - cursor_line
                if lines_to_jump:
                    print(f"\033[{lines_to_jump}B\r", end="")

            # Force a flush to return the cursor to the bottom immediately
            print("", end="", flush=True)

        self._last_printed = self._to_print.copy()
        self._to_print.clear()

    def clear_last_printed_lines(self) -> None:
        # Clear all the lines that were just printed
        print(
            f"{constants.CLEAR_LINE}{constants.UP_LINE}{constants.CLEAR_LINE}"
            * len(self._last_printed),
            end="",
        )

    def reset(self) -> None:
        self._last_printed.clear()
        self._to_print.clear()


class NonInteractiveConsolePrinter(ConsolePrinter):
    def __init__(self, colours: Colours | None = None, timer: bool = False) -> None:
        super().__init__(colours, timer)
        self._current_process: Process | None = None

    def print(self, process_group_manager: ProcessGroupManager) -> None:
        outputs = process_group_manager.cur_output
        for pg in outputs.process_group_outputs.values():
            for output in pg.processes:
                if self._current_process is None:
                    self._current_process = output.process
                    output = process_group_manager.get_process(output.id)
                    self.print_process_output(
                        output, include_progress=False, include_timer=False
                    )
                elif self._current_process is not output.process:
                    continue
                else:
                    self.print_process_output(output, include_cmd=False)

                if output.process.poll() is not None:
                    self.print_process_output(output, include_output=False)
                    self._current_process = None

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
        print("", end="", flush=True)
