from __future__ import annotations

import signal
import subprocess
import threading
import time
import typing

from pyallel.errors import InvalidLinesModifierError

if typing.TYPE_CHECKING:
    from io import BufferedReader


class ProcessOutput:
    def __init__(self, id: int, process: Process, data: str = "") -> None:  # noqa: A002
        self.id = id
        self.data = data
        self.lines = len(data.splitlines()) + 1
        self.process = process

    def merge(self, other: ProcessOutput) -> None:
        self.data += other.data
        self.lines += len(other.data.splitlines())


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
        self._lock = threading.Lock()

    def run(self) -> None:
        self.start = time.perf_counter()
        self._process = subprocess.Popen(  # noqa: S602
            self.command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
        )

        def _read_stdout() -> None:
            if self._process.stdout:
                stdout = typing.cast("BufferedReader", self._process.stdout)
                while True:
                    data = stdout.read1(65536)
                    if not data:
                        break
                    with self._lock:
                        self._buffer += data

        read_thread = threading.Thread(target=_read_stdout, daemon=True)
        read_thread.start()

    def poll(self) -> int | None:
        poll = self._process.poll()
        if poll is not None and not self.end:
            self.end = time.perf_counter()
        return poll

    def read(self) -> bytes:
        with self._lock:
            buffer = self._buffer
            self._buffer = b""

        return buffer

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
    def from_command(cls, id: int, command: str) -> Process:  # noqa: A002
        cmd = command.split(" :::: ", maxsplit=1)
        if len(cmd) == 1:
            return cls(id, cmd[0])

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

        return cls(id, " ".join(parts), round(percentage_lines / 100, 2))
