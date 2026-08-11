from __future__ import annotations

import signal
import subprocess
import time
from io import BufferedReader
from typing import Any

from typing_extensions import TypeGuard

from pyallel.errors import InvalidLinesModifierError


class ProcessOutput:
    def __init__(
        self,
        id: int,  # noqa: A002
        data: str = "",
        allocated_lines: int = 0,
        allocated_percentage_lines: float = 0.0,
        start: float = 0.0,
        end: float = 0.0,
        poll: int | None = None,
        command: str = "",
    ) -> None:
        self.id = id
        self.data = data
        self.lines = len(data.splitlines()) + 1
        self.allocated_lines = allocated_lines
        self.allocated_percentage_lines = allocated_percentage_lines
        self.start = start
        self.end = end
        self.poll = poll
        self.command = command

    def merge(self, other: ProcessOutput) -> None:
        if self.id != other.id:
            raise ValueError(f"Cannot merge process outputs with different ids: {self.id=}, {other.id=}")

        self.data += other.data
        self.lines += len(other.data.splitlines())
        self.allocated_lines = other.allocated_lines
        self.allocated_percentage_lines = other.allocated_percentage_lines
        self.start = other.start
        self.end = other.end
        self.poll = other.poll


class Process:
    def __init__(self, id: int, command: str, percentage_lines: float = 0.0) -> None:  # noqa: A002
        self.id = id
        self.command = command
        self.start = 0.0
        self.end = 0.0
        self.lines = 0
        self.percentage_lines = percentage_lines
        self._process: subprocess.Popen[bytes]
        self._buffer: bytes = b""
        self._stdout: BufferedReader

    def run(self) -> None:
        self.start = time.perf_counter()
        self._process = subprocess.Popen(  # noqa: S602
            self.command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
        )
        if not _is_buffered_reader(self._process.stdout):
            raise TypeError(f"Expected stdout to be a BufferedReader, got {self._process.stdout.__class__}")
        self._stdout = self._process.stdout

    def fileno(self) -> int:
        return self._stdout.fileno()

    def fetch_stdout(self) -> bool:
        data = self._stdout.read1(65536)
        if not data:
            if not self.end:
                self.end = time.perf_counter()
            return False

        self._buffer += data
        return True

    def poll(self, *, fetch_stdout: bool = True) -> int | None:
        poll = self._process.poll()
        if poll is not None and not self.end:
            if not self.end:
                self.end = time.perf_counter()
            # The process has exited, so drain whatever output is left
            # sitting in the pipe now rather than waiting for the selector to
            # notice it, otherwise trailing output written right before exit
            # can be missed
            if fetch_stdout:
                while self.fetch_stdout():
                    pass
        return poll

    def read(self) -> bytes:
        buffer = self._buffer
        self._buffer = b""
        return buffer

    def return_code(self) -> int | None:
        return self._process.returncode

    def interrupt(self) -> None:
        self._process.send_signal(signal.SIGINT)

    def kill(self) -> None:
        self._process.send_signal(signal.SIGKILL)

    def wait(self) -> int:
        return self._process.wait()

    @classmethod
    def from_command(cls, id: int, command: str) -> Process:  # noqa: A002
        cmd = command.split(" :::: ", maxsplit=1)
        if len(cmd) == 1:
            return cls(id, cmd[0].strip())

        args, *parts = cmd

        percentage_lines = 0
        for arg in args.split(" "):
            try:
                name, value = arg.split("=")
            except ValueError:
                continue

            if name == "lines":
                try:
                    percentage_lines = int(value)
                except ValueError:
                    raise InvalidLinesModifierError("lines modifier must be a number between 1 and 100")

                if not 0 < percentage_lines <= 100:  # noqa: PLR2004
                    raise InvalidLinesModifierError("lines modifier must be a number between 1 and 100")

                break

        return cls(id, " ".join(parts).strip(), round(percentage_lines / 100, 2))


def _is_buffered_reader(stdout: Any) -> TypeGuard[BufferedReader]:
    return isinstance(stdout, BufferedReader)
