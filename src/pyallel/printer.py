from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Protocol

from pyallel import constants
from pyallel.colours import Colours
from pyallel.constants import HIDE_CURSOR, SHOW_CURSOR

if TYPE_CHECKING:
    from pyallel.process import ProcessOutput
    from pyallel.process_group import ProcessGroupOutput


logger = logging.getLogger(__name__)


class Printer(Protocol):
    def print(self, output: ProcessGroupOutput, *, done: bool = False) -> None: ...


class ConsolePrinter:
    def __init__(self, colours: Colours | None = None, *, include_timer: bool = False) -> None:
        self._colours = colours or Colours()
        self._include_timer = include_timer
        self._prefix = f"{self._colours.dim_on}=>{self._colours.dim_off} "


class InteractiveConsolePrinter(ConsolePrinter):
    def __init__(self, colours: Colours | None = None, *, timer: bool = False) -> None:
        super().__init__(colours, include_timer=timer)
        self._cur_output: ProcessGroupOutput | None = None
        self._last_printed: list[tuple[bool, str, str]] = []
        self._buffer: list[str] = []
        self._last_progress_spinner_render = 0.0
        self._icon = 0

    def print(self, output: ProcessGroupOutput, *, done: bool = False) -> None:
        if self._cur_output is None:
            self._cur_output = output
        else:
            self._cur_output.merge(output)

        self.print_process_group_output(self._cur_output, interrupt_count=output.interrupt_count)

        if done:
            self.clear_last_printed_lines()
            self.reset()
            self.print_process_group_output(self._cur_output, interrupt_count=output.interrupt_count, tail_output=False)
            self.reset()

    def print_process_group_output(
        self,
        output: ProcessGroupOutput,
        *,
        interrupt_count: int = 0,
        tail_output: bool = True,
    ) -> None:
        columns = constants.columns()
        to_print = self.generate_process_group_output(output, interrupt_count=interrupt_count, tail_output=tail_output)

        num_lines_to_print = len(to_print)
        num_last_printed_lines = len(self._last_printed)

        # If we don't have any last printed lines or we don't want to tail the output,
        # we just print all the new lines
        if not num_last_printed_lines or not tail_output:
            for include_prefix, line, end in to_print:
                self._write(line, include_prefix=include_prefix, end=end, truncate=False, columns=columns)
        else:
            # Compare the number of last lines and new lines and only update what has changed.
            #
            # Move the cursor up the amount the lines that were last printed so we can start
            # comparing the last printed lines with the new lines that were generated
            self._output(f"\033[{num_last_printed_lines}A")
            cursor_line = 0
            for cur_line, line_parts in enumerate(self._last_printed[:num_lines_to_print]):
                # If the current line is not the same as it's newly generated version, we update the line
                if line_parts[1] != to_print[cur_line][1]:
                    include_prefix, line, end = to_print[cur_line]
                    # Jump to the line that needs to be changed
                    lines_to_jump = cur_line - cursor_line
                    if lines_to_jump:
                        self._output(f"\033[{lines_to_jump}B\r")
                    # Clear the current line
                    self._output(f"{constants.CLEAR_LINE}\r")
                    # Write the new line, this will move the cursor to the next line automatically
                    self._write(line, include_prefix=include_prefix, end=end, truncate=tail_output, columns=columns)
                    # Need to set the cursor_line to be the current line + 1 as the above write
                    # will move the cursor to the next line
                    cursor_line = cur_line + 1

            if num_lines_to_print > num_last_printed_lines:
                # Jump to the start of the new lines that needs to be printed
                lines_to_jump = num_last_printed_lines - cursor_line
                if lines_to_jump:
                    self._output(f"\033[{lines_to_jump}B\r")

                # Just print the new lines as normal
                for line_parts in to_print[num_last_printed_lines:]:
                    include_prefix, line, end = line_parts
                    self._write(line, include_prefix=include_prefix, end=end, truncate=tail_output, columns=columns)
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
        self._last_printed = to_print

    def generate_process_group_output(
        self,
        output: ProcessGroupOutput,
        *,
        interrupt_count: int = 0,
        tail_output: bool = True,
    ) -> list[tuple[bool, str, str]]:
        self.set_process_lines(output, interrupt_count)

        to_print: list[tuple[bool, str, str]] = []
        for out in output.processes:
            to_print.extend(self.generate_process_output(out, tail_output=tail_output))

        if interrupt_count == 1:
            to_print.append((False, "", "\n"))
            to_print.append(
                (
                    False,
                    f"{self._colours.yellow_bold}Interrupt!{self._colours.reset_colour}",
                    "\n",
                )
            )
        elif interrupt_count == 2:  # noqa: PLR2004
            to_print.append((False, "", "\n"))
            to_print.append(
                (
                    False,
                    f"{self._colours.red_bold}Abort!{self._colours.reset_colour}",
                    "\n",
                )
            )

        return to_print

    def generate_process_output(
        self, output: ProcessOutput, *, tail_output: bool = False
    ) -> list[tuple[bool, str, str]]:
        out: list[tuple[bool, str, str]] = []

        if tail_output and output.allocated_lines == 0:
            return out

        out.append((False, self.generate_process_output_status(output), "\n"))

        lines = output.data.splitlines()

        if tail_output:
            output_lines = output.allocated_lines - 1
            lines = [] if output_lines == 0 else lines[-output_lines:]

        for line in lines:
            end = line[-1] if line else ""
            if end != "\n":
                end = "\n"

            out.append((True, line, end))

        return out

    def generate_process_output_status(self, output: ProcessOutput, *, columns: int | None = None) -> str:
        columns = columns or constants.columns()
        passed = None
        icon = ""
        cur_time = time.perf_counter()
        end = output.end
        if not end:
            end = cur_time
        elapsed = end - output.start
        if output.poll is not None:
            passed = output.poll == 0
        if elapsed - self._last_progress_spinner_render >= constants.MAX_WAIT_BETWEEN_RENDERS:
            self._icon = (self._icon + 1) % len(constants.ICONS)
            self._last_progress_spinner_render = elapsed
        icon = constants.ICONS[self._icon]

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
        if self._include_timer:
            timer = f"({format_time_taken(elapsed)})"

        command = output.command
        status = f"{self._colours.white_bold}[{self._colours.reset_colour}{self._colours.blue_bold}{command}{self._colours.reset_colour}{self._colours.white_bold}]{self._colours.reset_colour}{colour} {msg} {icon}{self._colours.reset_colour}"
        if get_num_lines(status, columns) > 1:
            columns = columns - (len(msg) + len(timer) + 9)
            command = truncate_line(command, columns)
            status = f"{self._colours.white_bold}[{self._colours.reset_colour}{self._colours.blue_bold}{command}{self._colours.reset_colour}{self._colours.white_bold}]{self._colours.reset_colour}{colour} {msg} {icon}{self._colours.reset_colour}"

        if timer:
            status += f" {self._colours.dim_on}{timer}{self._colours.dim_off}"

        return status

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
            if not process_output.allocated_percentage_lines:
                processes_with_dynamic_lines.append(process_output)
                continue

            process_output.allocated_lines = int(lines * process_output.allocated_percentage_lines)
            used_lines += process_output.allocated_lines

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
                    process_output.command,
                    process_output.lines,
                    allocated_process_lines,
                )
                if process_output.lines < allocated_process_lines:
                    logger.debug(
                        "process [%s] lines less than allocated, reducing allocated lines to %s",
                        process_output.command,
                        process_output.lines,
                    )
                    process_output.allocated_lines = process_output.lines
                    lines -= process_output.allocated_lines
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
                    logger.debug("allocating %d lines to process [%s]", allocated_process_lines, process_output.command)
                    process_output.allocated_lines = allocated_process_lines
                    lines -= allocated_process_lines
                    logger.debug("new available screen lines = %d", lines)

                # If there is any lines left, allocate them to the process that currently contains the most lines in its output, or
                # allocate them to the first process if no process contains enough lines
                if lines:
                    logger.debug("remaining lines after allocation to all processes = %d", lines)
                    process_with_most_lines: ProcessOutput | None = None
                    most_lines = 0
                    for process_output in output.processes:
                        if process_output.allocated_lines > most_lines:
                            process_with_most_lines = process_output
                            most_lines = process_output.allocated_lines

                    if not process_with_most_lines:
                        logger.debug(
                            "no process found with most output, allocating remaining lines to first process [%s]",
                            process_output.command,
                        )
                        p_output = output.processes[0]
                        p_output.allocated_lines += lines
                        logger.debug("process [%s] allocated lines = %d", p_output.command, p_output.allocated_lines)
                    else:
                        logger.debug(
                            "found process [%s] with most output, allocating remaining lines",
                            process_output.command,
                        )
                        process_with_most_lines.allocated_lines += lines
                        logger.debug(
                            "process [%s] allocated lines = %d",
                            process_with_most_lines.command,
                            process_with_most_lines.allocated_lines,
                        )

                break

        logger.debug("all screen lines have been allocated")

    def clear_last_printed_lines(self) -> None:
        # Clear all the lines that were just printed
        self._output(f"{constants.CLEAR_LINE}{constants.UP_LINE}{constants.CLEAR_LINE}" * len(self._last_printed))
        self._flush_buffer()

    def reset(self) -> None:
        self._last_printed.clear()

    def show_cursor(self) -> None:
        print(constants.SHOW_CURSOR, end="", flush=True)

    def _write(
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
            if get_num_lines(line, columns) > 1:
                line = truncate_line(line, columns)
        self._output(f"{self._colours.reset_colour}{prefix}{line}", end=end, flush=flush)

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


class NonInteractiveConsolePrinter(ConsolePrinter):
    def __init__(self, colours: Colours | None = None, *, timer: bool = False) -> None:
        super().__init__(colours, include_timer=timer)
        # self._current_process: Process | None = None
        self._cur_pg_output: ProcessGroupOutput | None = None
        self._p_new = True
        self._p_index = 0
        self._generated_lines: list[tuple[bool, str, str]] = []

    def print(self, output: ProcessGroupOutput, *, done: bool = False) -> None:
        if self._cur_pg_output is None:
            self._cur_pg_output = output
        else:
            self._cur_pg_output.merge(output)

        try:
            p_output = output.processes[self._p_index]
        except IndexError:
            return

        if self._p_new:
            self._p_new = False
            p_output = self._cur_pg_output.processes[self._p_index]
            header = self.generate_process_header(p_output.command)
            self._write(header)

        self.print_process_output(p_output)

        if p_output.poll is not None:
            self._p_new = True
            self._p_index += 1
            header = self.generate_process_footer(p_output)
            self._write(header)

    def print_process_output(self, output: ProcessOutput) -> None:
        for include_prefix, line, end in self.generate_process_output(output):
            self._write(line, include_prefix=include_prefix, end=end)

        # Force a flush otherwise lines that don't end in a newline character will not get printed as they are read
        print(end="", flush=True)

    def generate_process_header(self, command: str) -> str:
        status = (
            f"{self._colours.white_bold}"
            f"[{self._colours.reset_colour}"
            f"{self._colours.blue_bold}{command}{self._colours.reset_colour}"
            f"{self._colours.white_bold}]{self._colours.reset_colour}"
            f"{self._colours.white_bold} running...{self._colours.reset_colour}"
        )
        out = (False, status, "\n")
        self._generated_lines.append(out)

        return status

    def generate_process_footer(self, output: ProcessOutput) -> str:
        icon = ""
        passed = None
        if output.poll is not None:
            passed = output.poll == 0

        if passed:
            colour = self._colours.green_bold
            msg = "done"
            icon = constants.TICK
        else:
            colour = self._colours.red_bold
            msg = "failed"
            icon = constants.X

        timer = ""
        if self._include_timer:
            cur_time = time.perf_counter()
            end = output.end
            if not end:
                end = cur_time
            elapsed = end - output.start
            timer = f"({format_time_taken(elapsed)})"

        status = (
            f"{self._colours.white_bold}"
            f"[{self._colours.reset_colour}"
            f"{self._colours.blue_bold}{output.command}{self._colours.reset_colour}"
            f"{self._colours.white_bold}]{self._colours.reset_colour}"
            f"{self._colours.white_bold} {msg} {icon}{self._colours.reset_colour}"
        )

        if timer:
            status += f" {self._colours.dim_on}{timer}{self._colours.dim_off}"

        out = (False, status, "\n")
        self._generated_lines.append(out)

        return status

    def generate_process_output(self, output: ProcessOutput) -> list[tuple[bool, str, str]]:
        out: list[tuple[bool, str, str]] = []
        lines = output.data.splitlines(keepends=True)

        for line in lines:
            prefix = True
            content = line[:-1]
            end = line[-1]

            try:
                prev_line = self._generated_lines[-1]
            except IndexError:
                pass
            else:
                if prev_line[2] != "\n":
                    prefix = False

            line_parts = (prefix, content, end)
            out.append(line_parts)
            self._generated_lines.append(line_parts)

        return out

    def _write(self, line: str, *, include_prefix: bool = False, end: str = "\n", flush: bool = False) -> None:
        prefix = self._prefix if include_prefix else ""
        print(f"{self._colours.reset_colour}{prefix}{line}", end=end, flush=flush)


def format_time_taken(time_taken: float) -> str:
    time_taken = round(time_taken, 1)
    seconds = time_taken % (24 * 3600)

    return f"{seconds}s"


def get_num_lines(line: str, columns: int | None = None) -> int:
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


def truncate_line(line: str, columns: int | None = None) -> str:
    columns = columns or constants.columns()
    escaped_line = constants.ANSI_ESCAPE.sub("", line)
    return "".join(escaped_line[:columns]) + "..."
