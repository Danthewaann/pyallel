from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Protocol

from pyallel import constants
from pyallel.colours import Colours
from pyallel.constants import HIDE_CURSOR, SHOW_CURSOR

if TYPE_CHECKING:
    from pyallel.process import Process, ProcessOutput
    from pyallel.process_group import ProcessGroupOutput
    from pyallel.process_group_manager import ProcessGroupManager


logger = logging.getLogger(__name__)


class Printer(Protocol):
    def print(self, process_group_manager: ProcessGroupManager) -> None:
        """Print output obtained from the provided process group manager.

        Args:
            process_group_manager: manager to obtain output from
        """


class ConsolePrinter:
    def __init__(self, colours: Colours | None = None, *, timer: bool = False) -> None:
        self._colours = colours or Colours()
        self._timer = timer
        self._prefix = f"{self._colours.dim_on}=>{self._colours.dim_off} "
        self._icon = 0
        self._to_print: list[tuple[bool, str, str]] = []

    def write(
        self,
        line: str,
        *,
        include_prefix: bool = False,
        end: str = "\n",
        flush: bool = False,
        truncate: bool = False,
        columns: int | None = None,
    ) -> None:
        truncate_num = 0
        prefix = self._prefix if include_prefix else ""
        columns = columns or constants.columns()
        if prefix:
            truncate_num = 6
        if prefix and truncate:
            columns = columns - truncate_num
            if self.get_num_lines(line, columns) > 1:
                line = self.truncate_line(line, columns)
        self._output(f"{self._colours.reset_colour}{prefix}{line}", end=end, flush=flush)

    def _output(self, s: str, *, end: str = "", flush: bool = False) -> None:
        print(s, end=end, flush=flush)

    def generate_process_output(
        self,
        output: ProcessOutput,
        *,
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
                output, include_progress=include_progress, include_timer=include_timer
            )
            line_parts = (False, status, "\n")
            out.append(line_parts)
            self._to_print.append(line_parts)

        if include_output:
            lines = output.data.splitlines(keepends=True)

            if tail_output:
                output_lines = output.process.lines - 1
                lines = [] if output_lines == 0 else lines[-output_lines:]

            for line in lines:
                prefix = True
                end = line[-1]
                if append_newlines and end != "\n":
                    end = "\n"
                else:
                    line = line[:-1]  # noqa: PLW2901

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
        *,
        include_progress: bool = True,
        include_timer: bool | None = None,
        columns: int | None = None,
    ) -> str:
        include_timer = include_timer if include_timer is not None else self._timer
        columns = columns or constants.columns()

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
        out = f"{self._colours.white_bold}[{self._colours.reset_colour}{self._colours.blue_bold}{command}{self._colours.reset_colour}{self._colours.white_bold}]{self._colours.reset_colour}{colour} {msg} {icon}{self._colours.reset_colour}"
        if self.get_num_lines(out, columns) > 1:
            columns = columns - (len(msg) + len(timer) + 9)
            command = self.truncate_line(command, columns)
            out = f"{self._colours.white_bold}[{self._colours.reset_colour}{self._colours.blue_bold}{command}{self._colours.reset_colour}{self._colours.white_bold}]{self._colours.reset_colour}{colour} {msg} {icon}{self._colours.reset_colour}"

        if timer:
            out += f" {self._colours.dim_on}{timer}{self._colours.dim_off}"

        return out

    def generate_process_group_output(
        self,
        output: ProcessGroupOutput,
        *,
        interrupt_count: int = 0,
        tail_output: bool = True,
    ) -> list[tuple[bool, str, str]]:
        self.set_process_lines(output, interrupt_count)

        for out in output.processes:
            self.generate_process_output(out, tail_output=tail_output, append_newlines=True)

        if interrupt_count == 1:
            self._to_print.append((False, "", "\n"))
            self._to_print.append(
                (
                    False,
                    f"{self._colours.yellow_bold}Interrupt!{self._colours.reset_colour}",
                    "\n",
                )
            )
        elif interrupt_count == 2:  # noqa: PLR2004
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

    def set_process_lines(  # noqa: PLR0915
        self,
        output: ProcessGroupOutput,
        interrupt_count: int = 0,
        lines: int = 0,
    ) -> None:
        lines = lines or constants.lines() - 1
        if interrupt_count:
            lines -= 2

        logger.debug("initial available lines in screen = %d", lines)
        # Allocate lines to processes that have a fixed percentage of lines set
        allocated_process_lines = lines // len(output.processes)
        logger.debug("initial allocated_process_lines = %d", allocated_process_lines)
        processes_with_dynamic_lines: list[ProcessOutput] = []
        used_lines = 0
        for process_output in output.processes:
            # This process output doesn't have percentage_lines set, so skip it
            if not process_output.process.percentage_lines:
                processes_with_dynamic_lines.append(process_output)
                continue

            process_output.process.lines = int(lines * process_output.process.percentage_lines)
            used_lines += process_output.process.lines

        # Remove the used lines from the total available lines
        lines -= used_lines
        logger.debug("available lines after allocating percentage lines = %d", lines)

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
                logger.debug(
                    "process [%s] lines = %d, allocated = %d",
                    process_output.process.command,
                    process_output.lines,
                    allocated_process_lines,
                )
                if process_output.lines < allocated_process_lines:
                    logger.debug(
                        "process [%s] lines less than allocated, reducing allocated lines to %s",
                        process_output.process.command,
                        process_output.lines,
                    )
                    process_output.process.lines = process_output.lines
                    lines -= process_output.process.lines
                    logger.debug("new available screen lines = %d", lines)
                    recalculate_lines = True
                    continue

                processes_with_excess_output.append(process_output)

            # We need to re-calcuate how many terminal lines we can allocate to each process if the output of at least one process
            # contains less lines than what we would normally allocate it. This is done so we can allocate these extra lines to the
            # other processes that contain more lines of output.
            if recalculate_lines:
                logger.debug("recalcuting available screen lines")
                processes_with_dynamic_lines = processes_with_excess_output
            else:
                # All remaining processes exceed the number of terminal lines we will allocate them, so allocate them
                # their terminal lines as normal and break out of the while loop
                for process_output in processes_with_excess_output:
                    logger.debug(
                        "allocating %d lines to process [%s]", allocated_process_lines, process_output.process.command
                    )
                    process_output.process.lines = allocated_process_lines
                    lines -= allocated_process_lines
                    logger.debug("new available screen lines = %d", lines)

                # If there is any lines left, allocate them to the process that currently contains the most lines in its output, or
                # allocate them to the first process if no process contains enough lines
                if lines:
                    logger.debug("remaining lines after allocation to all processes = %d", lines)
                    process_with_most_lines: ProcessOutput | None = None
                    most_lines = 0
                    for process_output in output.processes:
                        if process_output.process.lines > most_lines:
                            process_with_most_lines = process_output
                            most_lines = process_output.process.lines

                    if not process_with_most_lines:
                        logger.debug(
                            "no process found with most output, allocating remaining lines to first process [%s]",
                            process_output.process.command,
                        )
                        process = output.processes[0].process
                        process.lines += lines
                        logger.debug("process [%s] allocated lines = %d", process.command, process.lines)
                    else:
                        logger.debug(
                            "found process [%s] with most output, allocating remaining lines",
                            process_output.process.command,
                        )
                        process = process_with_most_lines.process
                        process.lines += lines
                        logger.debug("process [%s] allocated lines = %d", process.command, process.lines)

                break

        logger.debug("all screen lines have been allocated")

    def get_num_lines(self, line: str, columns: int | None = None) -> int:
        lines = 0
        columns = columns or constants.columns()
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
        columns = columns or constants.columns()
        escaped_line = constants.ANSI_ESCAPE.sub("", line)
        return "".join(escaped_line[:columns]) + "..."

    def format_time_taken(self, time_taken: float) -> str:
        time_taken = round(time_taken, 1)
        seconds = time_taken % (24 * 3600)

        return f"{seconds}s"


class InteractiveConsolePrinter(ConsolePrinter):
    def __init__(self, colours: Colours | None = None, *, timer: bool = False) -> None:
        super().__init__(colours, timer=timer)
        self._last_printed: list[tuple[bool, str, str]] = []
        self._buffer: list[str] = []

    def show_cursor(self) -> None:
        print(constants.SHOW_CURSOR, end="", flush=True)

    def _output(self, s: str, *, end: str = "", flush: bool = False) -> None:
        # Buffer everything for the current frame so it can be written to the
        # terminal in a single flush, rather than one write per line/escape
        # sequence, which is what causes the screen to flicker
        self._buffer.append(s)
        if end:
            self._buffer.append(end)
        if flush:
            self._flush_buffer()

    def _flush_buffer(self) -> None:
        if not self._buffer:
            return
        # Wrap the frame in a synchronized update so terminals that support it
        # apply the whole frame at once instead of rendering it as it arrives
        buffer = "".join(self._buffer)
        print(
            f"{constants.SYNC_UPDATE_BEGIN}{HIDE_CURSOR}{buffer}{SHOW_CURSOR}{constants.SYNC_UPDATE_END}",
            end="",
            flush=True,
        )
        self._buffer.clear()

    def print(self, process_group_manager: ProcessGroupManager) -> None:
        output = process_group_manager.get_cur_process_group_output()
        self.print_process_group_output(output, interrupt_count=process_group_manager.interrupt_count)

        poll = process_group_manager.poll()
        if poll is not None:
            self.clear_last_printed_lines()
            self.reset()
            self.print_process_group_output(
                output, interrupt_count=process_group_manager.interrupt_count, tail_output=False
            )
            self.reset()

    def print_process_group_output(
        self,
        output: ProcessGroupOutput,
        *,
        interrupt_count: int = 0,
        tail_output: bool = True,
    ) -> None:
        columns = constants.columns()
        self.generate_process_group_output(output, interrupt_count=interrupt_count, tail_output=tail_output)

        num_lines_to_print = len(self._to_print)
        num_last_printed_lines = len(self._last_printed)

        # If we don't have any last printed lines or we don't want to tail the output,
        # we just print all the new lines
        if not num_last_printed_lines or not tail_output:
            for include_prefix, line, end in self._to_print:
                self.write(line, include_prefix=include_prefix, end=end, truncate=tail_output, columns=columns)
        else:
            # Compare the number of last lines and new lines and only update what has changed.
            #
            # Move the cursor up the amount the lines that were last printed so we can start
            # comparing the last printed lines with the new lines that were generated
            self._output(f"\033[{num_last_printed_lines}A")
            cursor_line = 0
            for cur_line, line_parts in enumerate(self._last_printed[:num_lines_to_print]):
                # If the current line is not the same as it's newly generated version, we update the line
                if line_parts[1] != self._to_print[cur_line][1]:
                    include_prefix, line, end = self._to_print[cur_line]
                    # Jump to the line that needs to be changed
                    lines_to_jump = cur_line - cursor_line
                    if lines_to_jump:
                        self._output(f"\033[{lines_to_jump}B\r")
                    # Clear the current line
                    self._output(f"{constants.CLEAR_LINE}\r")
                    # Write the new line, this will move the cursor to the next line automatically
                    self.write(line, include_prefix=include_prefix, end=end, truncate=tail_output, columns=columns)
                    # Need to set the cursor_line to be the current line + 1 as the above write
                    # will move the cursor to the next line
                    cursor_line = cur_line + 1

            if num_lines_to_print > num_last_printed_lines:
                # Jump to the start of the new lines that needs to be printed
                lines_to_jump = num_last_printed_lines - cursor_line
                if lines_to_jump:
                    self._output(f"\033[{lines_to_jump}B\r")

                # Just print the new lines as normal
                for line_parts in self._to_print[num_last_printed_lines:]:
                    include_prefix, line, end = line_parts
                    self.write(line, include_prefix=include_prefix, end=end, truncate=tail_output, columns=columns)
            elif num_last_printed_lines > num_lines_to_print:
                # Make sure to clear the remaining last printed lines at the end of the screen so they don't get left behind
                self._output("\033[0J")
            else:
                # Jump to the end of the output since the num of lines printed hasn't changed
                lines_to_jump = num_lines_to_print - cursor_line
                if lines_to_jump:
                    self._output(f"\033[{lines_to_jump}B\r")

        # Write out the whole frame in a single flush so the terminal repaints
        # atomically instead of tearing across several small writes
        self._flush_buffer()

        self._last_printed = self._to_print.copy()
        self._to_print.clear()

    def clear_last_printed_lines(self) -> None:
        # Clear all the lines that were just printed
        self._output(f"{constants.CLEAR_LINE}{constants.UP_LINE}{constants.CLEAR_LINE}" * len(self._last_printed))
        self._flush_buffer()

    def reset(self) -> None:
        self._last_printed.clear()
        self._to_print.clear()


class NonInteractiveConsolePrinter(ConsolePrinter):
    def __init__(self, colours: Colours | None = None, *, timer: bool = False) -> None:
        super().__init__(colours, timer=timer)
        self._current_process: Process | None = None

    def print(self, process_group_manager: ProcessGroupManager) -> None:
        outputs = process_group_manager.cur_output
        for pg in outputs.process_group_outputs.values():
            for output in pg.processes:
                if self._current_process is None:
                    self._current_process = output.process
                    process_output = process_group_manager.get_process(output.id)
                    self.print_process_output(process_output, include_progress=False, include_timer=False)
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
        *,
        tail_output: bool = False,
        include_cmd: bool = True,
        include_output: bool = True,
        include_progress: bool = True,
        include_timer: bool | None = None,
    ) -> None:
        for include_prefix, line, end in self.generate_process_output(
            output,
            tail_output=tail_output,
            include_cmd=include_cmd,
            include_output=include_output,
            include_progress=include_progress,
            include_timer=include_timer,
        ):
            self.write(line, include_prefix=include_prefix, end=end)

        # Force a flush otherwise lines that don't end in a newline character will not get printed as they are read
        print(end="", flush=True)
