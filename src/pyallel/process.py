from __future__ import annotations

import signal
import subprocess
import tempfile
import time
from typing import BinaryIO


class ProcessOutput:
    def __init__(self, id: int, process: Process, data: str = "") -> None:
        self.id = id
        self.data = data
        self.process = process
        self.lines = -1

    def merge(self, other: ProcessOutput) -> None:
        self.data += other.data


class Process:
    def __init__(self, id: int, command: str) -> None:
        self.id = id
        self.command = command
        self.start = 0.0
        self.end = 0.0
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

