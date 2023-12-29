from __future__ import annotations

import time
import subprocess
import tempfile
import shlex
import shutil
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

from dataclasses import dataclass, field
from pyallel.errors import InvalidExecutableError


@dataclass
class ProcessGroup:
    processes: list[Process]
    output: dict[str, bytes] = field(default_factory=dict)

    def run(self) -> None:
        with ProcessPoolExecutor(max_workers=len(self.processes)) as executor:
            for process in self.processes:
                executor.submit(process.run)


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
        return Process(name=parsed_args[0], args=str_args, env=env)
