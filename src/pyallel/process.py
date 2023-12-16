from __future__ import annotations

import time
import subprocess
import shlex
import io
import shutil
import os
from typing import IO

from dataclasses import dataclass, field
from pyallel.errors import InvalidExecutableError


@dataclass
class Process:
    name: str
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)
    start: float = 0.0
    process: subprocess.Popen[bytes] | None = None

    def run(self) -> None:
        self.start = time.perf_counter()
        self.process = subprocess.Popen(
            [self.name, *self.args],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=self.env,
        )

    def poll(self) -> int | None:
        if self.process:
            return self.process.poll()
        return None

    def stdout(self) -> IO[bytes]:
        if self.process and self.process.stdout:
            return self.process.stdout
        return io.BytesIO(b"")

    def return_code(self) -> int | None:
        if self.process:
            return self.process.returncode
        return None

    @classmethod
    def from_command(cls, command: str) -> Process:
        env = os.environ.copy()
        args = command.split()
        parsed_args: list[str] = []
        for arg in args:
            if "=" in arg:
                name, value = arg.split("=")
                env[name] = value
            else:
                parsed_args.append(arg)

        if not shutil.which(parsed_args[0]):
            raise InvalidExecutableError(parsed_args[0])

        args = shlex.split(" ".join(parsed_args[1:]))
        return Process(name=parsed_args[0], args=args, env=env)
