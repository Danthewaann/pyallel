from __future__ import annotations

import signal
import subprocess
import tempfile
import time
from typing import BinaryIO

from pyallel.colours import Colours
from pyallel.errors import InvalidLinesModifierError


class ProcessOutput:
    def __init__(self, id: int, process: Process, data: str = "") -> None:
        self.id = id
        self.data = data
        self.lines = len(data.splitlines()) + 1
        self.process = process

    def merge(self, other: ProcessOutput) -> None:
        self.data += other.data
        self.lines += len(other.data.splitlines())


class Process:
    def __init__(
        self,
        id: int,
        command: str,
        display_command: str | None = None,
        percentage_lines: float = 0.0,
    ) -> None:
        self.id = id
        self.command = command
        self.display_command = display_command or command
        self.start = 0.0
        self.end = 0.0
        self.lines = 0
        self.percentage_lines = percentage_lines
        self._fd: BinaryIO
        self._process: subprocess.Popen[bytes]

    def run(self) -> None:
        self.start = time.perf_counter()
        fd, fd_name = tempfile.mkstemp()
        self._fd = open(fd_name, "rb")
        self._process = subprocess.Popen(
            self.command,
            stdin=subprocess.DEVNULL,
            stdout=fd,
            stderr=subprocess.STDOUT,
            shell=True,
        )

    def __del__(self) -> None:
        try:
            self._fd.close()
        except AttributeError:
            pass

    def poll(self) -> int | None:
        poll = self._process.poll()
        if poll is not None and not self.end:
            self.end = time.perf_counter()
        return poll

    def read(self) -> bytes:
        return self._fd.read()

    def readline(self) -> bytes:
        return self._fd.readline()

    def return_code(self) -> int | None:
        return self._process.returncode

    def interrupt(self) -> None:
        if hasattr(self, "_process"):
            self._process.send_signal(signal.SIGINT)

    def kill(self) -> None:
        if hasattr(self, "_process"):
            self._process.send_signal(signal.SIGKILL)

    def wait(self) -> int:
        return self._process.wait()

    @classmethod
    def from_command(
        cls, id: int, command: list[str], colours: Colours | None = None
    ) -> Process:
        try:
            split_index = command.index("::::")
        except ValueError:
            return cls(
                id,
                command=cls._convert_cmd(command, colours),
                display_command=" ".join(command),
            )

        args = command[:split_index]
        parts = command[split_index + 1 :]

        percentage_lines = 0
        for arg in args:
            try:
                arg, value = arg.split("=")
            except ValueError:
                continue

            if arg == "lines":
                try:
                    percentage_lines = int(value)
                except ValueError:
                    raise InvalidLinesModifierError(
                        "lines modifier must be a number between 1 and 100"
                    )

                if not 0 < percentage_lines <= 100:
                    raise InvalidLinesModifierError(
                        "lines modifier must be a number between 1 and 100"
                    )

                break

        return cls(
            id,
            command=cls._convert_cmd(parts[0].split(), colours),
            display_command=" ".join(command),
            percentage_lines=round(percentage_lines / 100, 2),
        )

    @classmethod
    def _convert_cmd(cls, command: list[str], colours: Colours | None = None) -> str:
        if colours and colours.enabled():
            converted_cmd: list[str] = []
            added_unbuffer = False
            for part in command:
                if not added_unbuffer:
                    is_env_var = len(part.split("=")) > 1
                    if is_env_var:
                        converted_cmd.append(part)
                        converted_cmd.extend(("unbuffer", "-nottycopy"))
                        added_unbuffer = True
                    else:
                        converted_cmd.extend(("unbuffer", "-nottycopy"))
                        converted_cmd.append(part)
                        added_unbuffer = True
                else:
                    converted_cmd.append(part)
            command = converted_cmd

        return " ".join(command)
