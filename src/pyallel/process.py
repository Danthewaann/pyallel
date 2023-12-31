from __future__ import annotations

import time
import subprocess
import tempfile
import shlex
import shutil
import os
from pathlib import Path
from uuid import UUID, uuid4
from typing import BinaryIO
from pyallel import constants

from dataclasses import dataclass, field
from pyallel.errors import InvalidExecutableErrors, InvalidExecutableError


def indent(output: str) -> str:
    return "\n".join("    " + line for line in output.splitlines())


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


def print_command_status(process: Process, passed: bool, debug: bool = False) -> None:
    colour = constants.RED_BOLD
    msg = "failed"
    icon = constants.X
    if passed:
        colour = constants.GREEN_BOLD
        msg = "done"
        icon = constants.TICK

    print(f"[{constants.BLUE_BOLD}{process.name}", end="")

    if debug:
        print(f" {' '.join(process.args)}", end="")

    print(f"{constants.NC}]{colour} {msg} ", end="")

    if debug:
        elapsed = time.perf_counter() - process.start
        print(f"in {format_time_taken(elapsed)} ", end="")

    print(f"{icon}{constants.NC}")


def print_command_output(process: Process) -> None:
    output = process.read()
    if output:
        print(f"{indent(output.decode())}")
    print()


def run_process(process: Process, debug: bool = False) -> bool:
    print(f"{constants.CLEAR_LINE}{constants.CR}", end="")

    if process.return_code() != 0:
        print_command_status(process, passed=False, debug=debug)
        print_command_output(process)
        return False
    else:
        print_command_status(process, passed=True, debug=debug)
        print_command_output(process)
        return True


@dataclass
class ProcessGroup:
    processes: list[Process]
    fail_fast: bool = False
    interactive: bool = False
    debug: bool = False
    output: dict[UUID, str] = field(default_factory=dict)

    def run(self) -> bool:
        for process in self.processes:
            process.run()

        completed_processes: set[UUID] = set()
        passed = True

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
                if process.id in completed_processes or process.poll() is None:
                    continue

                completed_processes.add(process.id)
                passed = run_process(process, debug=self.debug)
                if self.fail_fast and not passed:
                    return False

            if len(completed_processes) == len(self.processes):
                break

        return passed

    def stream(self) -> bool:
        for process in self.processes:
            process.run()

        if not self.interactive:
            return self.stream_non_interactive()

        completed_processes: set[UUID] = set()
        passed = True

        while True:
            output = ""
            for i, process in enumerate(self.processes, start=1):
                output += f"[{process.name}] running...\n"
                process_output = process.read().decode()
                if process_output:
                    self.output[process.id] = process_output
                    output += "\n".join(indent(process_output).splitlines()[-10:])
                    output += "\n"
                    if i != len(self.processes):
                        output += "\n"

                if process.poll() is not None:
                    completed_processes.add(process.id)

            print(output)
            lines = len(output.splitlines()) + len(self.processes)
            for _ in range(lines - (len(self.processes) - 1)):
                print(f"{constants.CLEAR_LINE}\033[1F", end="")

            if len(completed_processes) == len(self.processes):
                print(output)
                break

            time.sleep(0.05)

        return passed

    def stream_non_interactive(self) -> bool:
        completed_processes: set[UUID] = set()
        passed = True
        running_process = None

        while True:
            output = ""
            for i, process in enumerate(self.processes, start=1):
                if running_process is None and process.id not in completed_processes:
                    output += f"[{process.name}] running...\n"
                    running_process = process
                elif running_process is not process:
                    continue

                process_output = process.readline().decode()
                if process_output:
                    output += indent(process_output)
                    output += "\n"

                if process.poll() is not None:
                    completed_processes.add(process.id)
                    running_process = None

            if output:
                print(output, end="")

            if len(completed_processes) == len(self.processes):
                break

            time.sleep(0.05)

        return passed

    @classmethod
    def from_commands(
        cls,
        commands: list[str],
        interactive: bool = False,
        fail_fast: bool = False,
        debug: bool = False,
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
            fail_fast=fail_fast,
            debug=debug,
        )


@dataclass
class Process:
    id: UUID
    name: str
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)
    start: float = 0.0
    process: subprocess.Popen[bytes] | None = None
    output: bytes = b""
    fd_name: Path | None = None
    fd_read: BinaryIO | None = None
    fd: int | None = None

    def run(self) -> None:
        self.start = time.perf_counter()
        self.fd, fd_name = tempfile.mkstemp()
        self.fd_name = Path(fd_name)
        self.process = subprocess.Popen(
            [self.name, *self.args],
            stdout=self.fd,
            stderr=subprocess.STDOUT,
            env=self.env,
        )

    def __del__(self) -> None:
        if self.fd_read:
            self.fd_read.close()
        if self.fd_name:
            self.fd_name.unlink(missing_ok=True)

    def poll(self) -> int | None:
        if self.process:
            return self.process.poll()
        return None

    def read(self) -> bytes:
        if self.fd_name:
            return self.fd_name.read_bytes()
        return b""

    def readline(self) -> bytes:
        if self.fd_name:
            if not self.fd_read:
                self.fd_read = open(self.fd_name, "rb")
            return self.fd_read.readline()
        return b""

    def return_code(self) -> int | None:
        if self.process:
            return self.process.returncode
        return None

    @classmethod
    def from_command(cls, command: str) -> Process:
        env = os.environ.copy()
        if " :: " in command:
            command_modes, args = command.split(" :: ")
            command_modes = command_modes.split()
            args = args.split()
        else:
            args = command.split()
            command_modes = ""

        parsed_args: list[str] = []
        for arg in args:
            if "=" in arg:
                name, value = arg.split("=")
                env[name] = value
            else:
                parsed_args.append(arg)

        if not shutil.which(parsed_args[0]):
            raise InvalidExecutableError(parsed_args[0])

        str_args = shlex.split(" ".join(parsed_args[1:]))
        return cls(id=uuid4(), name=parsed_args[0], args=str_args, env=env)
