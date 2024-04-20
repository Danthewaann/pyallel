from __future__ import annotations

import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from typing import BinaryIO


@dataclass
class Process:
    id: int
    command: str
    start: float = 0.0
    end: float = 0.0
    _fd: BinaryIO | None = field(init=False, repr=False, compare=False, default=None)
    _process: subprocess.Popen[bytes] | None = field(
        init=False, repr=False, compare=False, default=None
    )

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
