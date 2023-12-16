from __future__ import annotations

import time
import subprocess
import shlex
import io
import shutil
import os
from typing import IO
import asyncio

from dataclasses import dataclass, field
from pyallel.errors import InvalidExecutableError


@dataclass
class Process:
    name: str
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)
    start: float = 0.0
    process: asyncio.subprocess.Process | None = None
    output: bytes = field(default_factory=bytes)

    async def run(self) -> None:
        self.start = time.perf_counter()
        self.process = await asyncio.create_subprocess_exec(
            self.name,
            *self.args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self.env
        )
        # self.process = subprocess.Popen(
        #     [self.name, *self.args],
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.STDOUT,
        #     env=self.env,
        # )

    async def wait(self) -> int:
        if self.process:
            return await self.process.wait()
        return -1

    async def stream(self) -> bytes:
        line = await self.stdout().readline()
        self.output += line
        return line

    async def read(self) -> bytes:
        out = await self.stdout().read()
        self.output += out
        return out

    # def poll(self) -> int | None:
    #     if self.process:
    #         return self.process.process
    #     return None

    def stdout(self) -> asyncio.StreamReader:
        if self.process and self.process.stdout:
            return self.process.stdout
        return asyncio.StreamReader()

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
