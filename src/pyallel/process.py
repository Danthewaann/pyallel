from __future__ import annotations

import time
import subprocess
import tempfile
import shlex
import shutil
import os
from pathlib import Path
from pyallel import contants

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
    colour = contants.RED_BOLD
    msg = "failed"
    icon = contants.X
    if passed:
        colour = contants.GREEN_BOLD
        msg = "done"
        icon = contants.TICK

    print(f"[{contants.BLUE_BOLD}{process.name}", end="")

    if debug:
        print(f" {' '.join(process.args)}", end="")

    print(f"{contants.NC}]{colour} {msg} ", end="")

    if debug:
        elapsed = time.perf_counter() - process.start
        print(f"in {format_time_taken(elapsed)} ", end="")

    print(f"{icon}{contants.NC}")


def print_command_output(process: Process) -> None:
    output = process.read()
    if output:
        print(f"{indent(output.decode())}")
    print()


def run_process(process: Process, debug: bool = False) -> bool:
    print(f"{contants.CLEAR_LINE}{contants.CR}", end="")

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
    output: dict[str, bytes] = field(default_factory=dict)

    def run(self) -> bool:
        for process in self.processes:
            process.run()

        completed_processes: set[str] = set()
        passed = True

        if not self.interactive or not contants.IN_TTY:
            print(f"{contants.WHITE_BOLD}Running commands...{contants.NC}\n")

        while True:
            if self.interactive and contants.IN_TTY:
                for icon in contants.ICONS:
                    print(
                        f"{contants.CLEAR_LINE}{contants.CR}{contants.WHITE_BOLD}Running commands{contants.NC} {icon}",
                        end="",
                    )
                    time.sleep(0.1)

            for process in self.processes:
                if process.name in completed_processes or process.poll() is None:
                    continue

                completed_processes.add(process.name)
                passed = run_process(process, debug=self.debug)
                if self.fail_fast and not passed:
                    return False

            if len(completed_processes) == len(self.processes):
                break

        return passed

    def stream(self) -> bool:
        completed_processes: set[str] = set()
        passed = True

        while True:
            for process in self.processes:
                print(f"[{process.name}] running...")
                output = process.read().decode()
                if output:
                    print(indent(process.output.decode()))

                if process.name in completed_processes:
                    continue

                lines = len(output.splitlines())

                if process.poll() is not None:
                    completed_processes.add(process.name)

                for line in range(lines):
                    print(f"{CLEAR_LINE}\033[1F", end="")

                # lines = sum(len(process.output.splitlines()) for process in processes)
                # print(f"\033[{lines +1}F{CLEAR_LINE}", end="")
                print(f"[{process.name}] running...")
                if process.output:
                    print(indent(process.output.decode()))

            if len(completed_processes) == len(self.processes):
                break

            time.sleep(0.1)
            # print(f"\033[{lines +1}F{CLEAR_LINE}", end="")
            # lines = sum(len(process.output.splitlines()) for process in processes)
            # print(lines)
            # for line in range(lines + 2):
            #     print(f"{CLEAR_LINE}\033[1F", end="")

            # old_command_output = command_output
            # print(f"{RESTORE_CURSOR}", end="")
            # print("\033]0J", end="")
            # print(f"{SAVE_CURSOR}", end="")
            # print(f"{CLEAR_SCREEN}", end="")
            # for _ in command_output.splitlines():
            #     print(f"{UP_LINE}{CLEAR_LINE}{CR}", end="")

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
    name: str
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)
    start: float = 0.0
    process: subprocess.Popen[bytes] | None = None
    output: bytes = b""
    fd_name: Path | None = None
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
        if self.fd_name:
            self.fd_name.unlink()

    def poll(self) -> int | None:
        if self.process:
            return self.process.poll()
        return None

    def read(self) -> bytes:
        if self.fd_name:
            return self.fd_name.read_bytes()
        return b""

    def stream(self) -> None:
        while self.poll() is None:
            for line in iter(self.process.stdout.readline, b""):
                self.output += line

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
        return cls(name=parsed_args[0], args=str_args, env=env)
