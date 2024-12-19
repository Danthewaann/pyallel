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
        self._fd: BinaryIO | None = None
        self._process: subprocess.Popen[bytes] | None = None

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

    def interrupt(self) -> None:
        if self._process:
            self._process.send_signal(signal.SIGINT)

    def kill(self) -> None:
        if self._process:
            self._process.send_signal(signal.SIGKILL)

    def wait(self) -> int:
        if self._process:
            return self._process.wait()
        return -1
