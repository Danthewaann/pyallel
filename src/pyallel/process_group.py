from __future__ import annotations

import selectors
from typing import Sequence

from pyallel.errors import (
    InvalidLinesModifierError,
)
from pyallel.process import Process, ProcessOutput


class ProcessGroupOutput:
    def __init__(self, id: int, processes: Sequence[ProcessOutput], interrupt_count: int = 0) -> None:  # noqa: A002
        self.id = id
        self.processes = processes
        self.interrupt_count = interrupt_count

    def merge(self, other: ProcessGroupOutput) -> None:
        if self.id != other.id:
            raise ValueError(f"Cannot merge process group outputs with different ids: {self.id=}, {other.id=}")
        for i, _ in enumerate(self.processes):
            self.processes[i].merge(other.processes[i])


class ProcessGroup:
    def __init__(self, id: int, processes: list[Process]) -> None:  # noqa: A002
        self.id = id
        self.processes = processes
        self._exit_code = 0
        self._interrupt_count = 0
        self._selector = selectors.DefaultSelector()

    @classmethod
    def from_commands(cls, id: int, process_id: int, *commands: str) -> ProcessGroup:  # noqa: A002
        cmds: list[str] = []
        processes: list[Process] = []

        percentage_lines_sum = 0.0
        for i, command in enumerate(commands):
            if command != "::":
                cmds.append(command)
                continue

            process = Process.from_command(i + process_id, " ".join(cmds))
            percentage_lines_sum += process.percentage_lines
            processes.append(process)
            cmds.clear()

        if cmds:
            process = Process.from_command(i + process_id, " ".join(cmds))
            percentage_lines_sum += process.percentage_lines
            processes.append(process)

        if round(percentage_lines_sum, 2) > 1.0:
            raise InvalidLinesModifierError(
                "lines modifier must not exceed 100 across all processes within each process group"
            )

        return cls(id=id, processes=processes)

    def run(self) -> None:
        for process in self.processes:
            process.run()
            self._selector.register(process.fileno(), selectors.EVENT_READ, data=process)

    def poll(self) -> int | None:
        polls: list[int | None] = [process.poll() for process in self.processes]

        running = [p for p in polls if p is None]
        failed = [p for p in polls if p is not None and p > 0]

        if running:
            return None
        if failed:
            return 1
        return 0

    def stream(self) -> ProcessGroupOutput:
        return ProcessGroupOutput(
            id=self.id,
            processes=[
                ProcessOutput(
                    id=process.id,
                    data=process.read().decode(),
                    allocated_lines=process.lines,
                    allocated_percentage_lines=process.percentage_lines,
                    start=process.start,
                    end=process.end,
                    poll=process.poll(fetch_stdout=False),
                    command=process.command,
                )
                for process in self.processes
            ],
            interrupt_count=self._interrupt_count,
        )

    def wait_for_update(self, timeout: float) -> None:
        # Block until either process output is ready to read or the timeout elapses
        for key, _ in self._selector.select(timeout):
            process: Process = key.data
            if not process.fetch_stdout():
                self._selector.unregister(key.fileobj)

    def handle_signal(self, _signum: int) -> None:
        for process in self.processes:
            if self._interrupt_count == 0:
                process.interrupt()
            else:
                process.kill()

        self._interrupt_count += 1
