from __future__ import annotations
from collections import defaultdict

import time
import subprocess
import tempfile
import shlex
import shutil
import os
from uuid import UUID, uuid4
from typing import BinaryIO
from pyallel import constants

from dataclasses import dataclass, field
from pyallel.errors import InvalidExecutableErrors, InvalidExecutableError


def get_num_lines(output: str, columns: int | None = None) -> int:
    lines = 0
    columns = columns or constants.COLUMNS()
    for line in output.splitlines():
        length = len(line)
        lines += 1 * (length % columns + 1 if length > columns else 1)
    return lines


def indent(output: str, keepend: bool = True) -> str:
    indented_output = "\n".join("    " + line for line in output.splitlines())
    if keepend and output and output[-1] == "\n":
        indented_output += "\n"
    return indented_output


def format_time_taken(time_taken: float) -> str:
    seconds = int(time_taken) % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    msg = ""
    if time_taken < 60:
        msg = f"{seconds}s"
    elif 60 <= time_taken < 3600:
        msg = f"{minutes}m"
        if seconds:
            msg += f" {seconds}s"
    elif time_taken >= 3600:
        msg = f"{hour}h"
        if minutes:
            msg += f" {minutes}m"
        if seconds:
            msg += f" {seconds}s"

    return msg


def get_command_status(
    process: Process,
    icon: str | None = None,
    passed: bool | None = None,
    verbose: bool = False,
    timer: bool = False,
) -> str:
    if passed is True:
        colour = constants.GREEN_BOLD
        msg = "done"
        icon = icon or constants.TICK
    elif passed is False:
        colour = constants.RED_BOLD
        msg = "failed"
        icon = icon or constants.X
    else:
        colour = constants.WHITE_BOLD
        msg = "running"
        icon = icon or ""
        if not icon:
            msg += "..."

    output = f"[{constants.BLUE_BOLD}{process.name}"

    if verbose:
        output += f" {' '.join(process.args)}"

    output += f"{constants.NC}]{colour} {msg} "

    if timer:
        end = process.end
        if not process.end:
            end = time.perf_counter()
        elapsed = end - process.start
        output += f"in {format_time_taken(elapsed)} "

    output += f"{icon}{constants.NC}"
    return output


def print_command_output(process: Process) -> None:
    output = process.read()
    if output:
        print(indent(output.decode(), keepend=False))
    print()


def run_process(process: Process, timer: bool = False, verbose: bool = False) -> bool:
    print(f"{constants.CLEAR_LINE}{constants.CR}", end="")

    if process.return_code() != 0:
        print(get_command_status(process, passed=False, verbose=verbose, timer=timer))
        print_command_output(process)
        return False
    else:
        print(get_command_status(process, passed=True, verbose=verbose, timer=timer))
        print_command_output(process)
        return True


@dataclass
class ProcessGroup:
    processes: list[Process]
    interactive: bool = False
    timer: bool = False
    verbose: bool = False
    output: dict[UUID, list[str]] = field(default_factory=lambda: defaultdict(list))
    process_lines: list[int] = field(default_factory=list)
    completed_processes: set[UUID] = field(default_factory=set)
    passed: bool = True
    icon: int = 0

    def run(self) -> bool:
        for process in self.processes:
            process.run()

        if not self.interactive or not constants.IN_TTY:
            print(f"{constants.WHITE_BOLD}Running commands...{constants.NC}\n")

        while True:
            if self.interactive and constants.IN_TTY:
                for icon in constants.ICONS:
                    print(
                        f"{constants.CLEAR_LINE}{constants.CR}{constants.WHITE_BOLD}Running commands{constants.NC} {icon}",
                        end="",
                    )
                    time.sleep(0.1)

            for process in self.processes:
                if process.id in self.completed_processes or process.poll() is None:
                    continue

                self.completed_processes.add(process.id)
                process_passed = run_process(
                    process, verbose=self.verbose, timer=self.timer
                )
                if not process_passed:
                    self.passed = False

            if len(self.completed_processes) == len(self.processes):
                break

        return self.passed

    def stream(self) -> bool:
        for process in self.processes:
            process.run()

        if not self.interactive:
            return self.stream_non_interactive()

        while True:
            output = self.complete_output()

            self.icon += 1
            if self.icon == len(constants.ICONS):
                self.icon = 0

            # Clear the screen and print the output
            print(f"\033[H\033[0J{output}", end="")

            # Clear the screen again
            print("\033[H\033[0J", end="")

            if len(self.completed_processes) == len(self.processes):
                break

            time.sleep(0.1)

        output = self.complete_output(all=True)
        # Clear the screen one final time before printing the output
        print(f"\033[3J{output}")
        return self.passed

    def stream_non_interactive(self) -> bool:
        running_process = None

        print(f"{constants.WHITE_BOLD}Running commands...{constants.NC}\n")

        while True:
            output = ""
            for process in self.processes:
                if (
                    running_process is None
                    and process.id not in self.completed_processes
                ):
                    output += get_command_status(process, verbose=self.verbose)
                    output += "\n"
                    running_process = process
                elif running_process is not process:
                    # Need to do this to properly keep track of how long all the other
                    # commands are taking
                    process.poll()
                    continue

                process_output = process.readline().decode()

                if not self.output[process.id] and process_output:
                    process_output = indent(process_output)
                    self.output[process.id].append(process_output)
                    output += process_output
                elif process_output:
                    if self.output[process.id][-1][-1] != "\n":
                        self.output[process.id][-1] += process_output
                    else:
                        process_output = indent(process_output)
                        self.output[process.id].append(process_output)
                    output += process_output

                if process.poll() is not None:
                    if process.return_code() != 0:
                        self.passed = False
                    process_output = process.read().decode()
                    if process_output:
                        output += indent(process_output)

                    output += get_command_status(
                        process,
                        passed=process.return_code() == 0,
                        verbose=self.verbose,
                        timer=self.timer,
                    )
                    output += "\n\n"
                    self.completed_processes.add(process.id)
                    running_process = None

            if output:
                print(output, end="")

            if len(self.completed_processes) == len(self.processes):
                break

            time.sleep(0.01)

        return self.passed

    @classmethod
    def from_commands(
        cls,
        *commands: str,
        interactive: bool = False,
        timer: bool = False,
        verbose: bool = False,
    ) -> ProcessGroup:
        processes: list[Process] = []
        errors: list[InvalidExecutableError] = []

        for command in commands:
            try:
                processes.append(Process.from_command(command))
            except InvalidExecutableError as e:
                errors.append(e)

        if errors:
            raise InvalidExecutableErrors(*errors)

        return cls(
            processes=processes,
            interactive=interactive,
            timer=timer,
            verbose=verbose,
        )

    def complete_output(self, tail: int = 20, all: bool = False) -> str:
        num_processes = len(self.processes)
        lines = constants.LINES() - (2 * num_processes)
        remainder = lines % num_processes
        tail = lines // num_processes

        if self.process_lines:
            self.process_lines = []

        for process in self.processes:
            self.process_lines.append(tail)

        if remainder:
            self.process_lines[-1] += remainder - 2
        else:
            self.process_lines[-1] -= 2

        output = ""
        for i, process in enumerate(self.processes, start=1):
            if process.poll() is not None:
                self.completed_processes.add(process.id)
                if process.return_code() != 0:
                    self.passed = False
                output += get_command_status(
                    process,
                    passed=process.return_code() == 0,
                    verbose=self.verbose,
                    timer=self.timer,
                )
                output += "\n"
            else:
                output += get_command_status(
                    process,
                    icon=constants.ICONS[self.icon],
                    verbose=self.verbose,
                    timer=self.timer,
                )
                output += "\n"

            process_output = process.read().decode()
            if not self.output[process.id]:
                self.output[process.id].append("")
            self.output[process.id][0] += process_output
            process_output = self.output[process.id][0]
            if process_output:
                if not all:
                    process_output = "\n".join(
                        process_output.splitlines()[-self.process_lines[i - 1] :]
                    )
                    process_output += "\n"
                output += indent(process_output)
                if output and output[-1] != "\n":
                    output += "\n"
                if i != num_processes:
                    output += "\n"

        return output


@dataclass
class DumpMode:
    enabled: bool = False


@dataclass
class Process:
    id: UUID = field(repr=False, compare=False)
    name: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    start: float = 0.0
    end: float = 0.0
    dump_mode: DumpMode = field(default_factory=DumpMode)
    _fd: BinaryIO | None = field(init=False, repr=False, compare=False, default=None)
    _process: subprocess.Popen[bytes] | None = field(
        init=False, repr=False, compare=False, default=None
    )

    def run(self) -> None:
        self.start = time.perf_counter()
        fd, fd_name = tempfile.mkstemp()
        self._fd = open(fd_name, "rb")
        self._process = subprocess.Popen(
            [self.name, *self.args],
            stdout=fd,
            stderr=subprocess.STDOUT,
            env=self.env,
        )

    def __del__(self) -> None:
        if self._fd:
            self._fd.close()

    def poll(self) -> int | None:
        if self._process:
            poll = self._process.poll()
            if poll is not None and not self.end:
                self.end = time.perf_counter()
            return poll
        return None

    def read(self) -> bytes:
        if self._fd:
            return self._fd.read()
        return b""

    def readline(self) -> bytes:
        if self._fd:
            return self._fd.readline()
        return b""

    def return_code(self) -> int | None:
        if self._process:
            return self._process.returncode
        return None

    @classmethod
    def from_command(cls, command: str) -> Process:
        dump_mode = DumpMode()
        env = os.environ.copy()
        if " :: " in command:
            modes, _args = command.split(" :: ")
            if modes:
                for mode in modes.split(","):
                    name, *_ = mode.split("=", maxsplit=1)
                    if name == "dump":
                        dump_mode.enabled = True
            args = _args.split()
        else:
            args = command.split()

        parsed_args: list[str] = []
        for arg in args:
            if "=" in arg:
                name, env_value = arg.split("=")
                env[name] = env_value
            else:
                parsed_args.append(arg)

        if not shutil.which(parsed_args[0]):
            raise InvalidExecutableError(parsed_args[0])

        str_args = shlex.split(" ".join(parsed_args[1:]))
        return cls(
            id=uuid4(),
            name=parsed_args[0],
            args=str_args,
            env=env,
            dump_mode=dump_mode,
        )
